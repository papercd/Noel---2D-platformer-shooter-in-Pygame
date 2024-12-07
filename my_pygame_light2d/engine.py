from importlib import resources
from enum import Enum
import numpy as np
import moderngl
import pygame
import numbers
from OpenGL.GL import glBlitNamedFramebuffer, GL_COLOR_BUFFER_BIT, GL_NEAREST, glGetUniformBlockIndex, glUniformBlockBinding
import math
import time
from scripts.new_HUD import HUD
from scripts.new_particles import ParticleSystem
from scripts.lists import TileCategories,interpolatedLightNode
from scripts.new_panel import TilePanel
from scripts.new_entities import Player
from scripts.new_cursor import Cursor
from scripts.custom_data_types import TileInfo
from scripts.layer import Layer_
from scripts.atlass_positions import UI_ATLAS_POSITIONS_AND_SIZES, TILE_ATLAS_POSITIONS,\
                                    ENTITIES_ATLAS_POSITIONS,TEXT_DIMENSIONS,TEXT_ATLAS_POSITIONS,PARTICLE_ATLAS_POSITIONS_AND_SIZES

from scripts.new_tilemap import Tilemap
from my_pygame_light2d.shader import Shader 
from my_pygame_light2d.light import PointLight
from my_pygame_light2d.hull import Hull
from my_pygame_light2d.color import normalize_color_arguments, denormalize_color
from my_pygame_light2d.double_buff import DoubleBuff
from my_pygame_light2d.util import create_rotated_rect,to_dest_coords

BASE_PATH = 'data/images/'


class RenderEngine:
    """A class for managing rendering for my game within a Pygame environment."""

    def __init__(self,context:moderngl.Context, screen_res: tuple[int, int],true_to_screen_res_ratio: float, true_res: tuple[int, int]  ) -> None:
        """
        Initialize the render engine.

        Args:
            context : the moderngl context 
            screen_res : the resolution of the display
            true_to_screen_res_ratio : the ratio of the screen resolution from the true resolution. 
            true_res:  (tuple[int, int]): true (native) resolution of the game (width, height) -pixel resolution.
        """


        # Initialize private members
        self._true_to_native_ratio = true_to_screen_res_ratio 
        self._screen_res = screen_res
        self._true_res = true_res 

        self._diagonal = math.sqrt(self._true_res[0] ** 2 + self._true_res[1] ** 2)
        self._lightmap_res = true_res 
        self._ambient = (.25, .25, .25, .25)

        # Objects that need to be bound to engine before rendering : 
        self._tilemap:Tilemap = None
        self._player:Player = None
        self._entities_atl: moderngl.Texture= None 
        self._background: list[moderngl.Texture]= None

        # Initialize public members
        self.lights: list[PointLight] = []
        self.hulls: list[Hull] = []
        self.shadow_blur_radius: int =5

        # Create an OpenGL context
        self.ctx = context

        # Load shaders
        self._load_shaders()

        # Create VAO and VBO
        self._create_screen_vertex_buffers()

        # Create render textures and corresponding FBOs
        self._create_frame_buffers()

        # Create SSBO for hull vertices
        self._create_ssbos()


    def _load_shaders(self):
        # Read source files
        with open('my_pygame_light2d/vertex.glsl',encoding='utf-8') as file:
            vertex_src = file.read()
        with open('my_pygame_light2d/shimmer_vertex.glsl',encoding='utf-8') as file:
            vertex_src_shimmer = file.read()

        with open('my_pygame_light2d/fragment_light.glsl',encoding='utf-8') as file:
            fragment_src_light= file.read()

        with open('my_pygame_light2d/fragment_blur.glsl',encoding='utf-8') as file:
            fragment_src_blur= file.read()

        with open('my_pygame_light2d/fragment_mask.glsl', encoding='utf-8') as file:
            fragment_src_mask = file.read()

        with open('my_pygame_light2d/fragment_draw.glsl', encoding='utf-8') as file:
            fragment_src_draw = file.read()
        
        with open('my_pygame_light2d/fragment_shimmer.glsl', encoding='utf-8') as file:
            fragment_src_shimmer = file.read()
   
        # Create shader programs
        self._prog_mask = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader= fragment_src_mask)

        self._prog_light = self.ctx.program(vertex_shader=vertex_src,
                                            fragment_shader=fragment_src_light)
        self._prog_blur = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader=fragment_src_blur)
        
        self._prog_draw = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader=fragment_src_draw)
        
        self._prog_shimmer = self.ctx.program(vertex_shader=vertex_src_shimmer,
                                              fragment_shader=fragment_src_shimmer)




    def _create_screen_vertex_buffers(self):
        # Screen mesh
        screen_vertices = np.array([(-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0),
                                    (-1.0, -1.0), (1.0, 1.0), (1.0, -1.0)], dtype=np.float32)
        screen_tex_coords = np.array([(0.0, 1.0), (1.0, 1.0), (0.0, 0.0),
                                      (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)], dtype=np.float32)
        screen_vertex_data = np.hstack([screen_vertices, screen_tex_coords])

        # VAO and VBO for screen mesh
        screen_vbo = self.ctx.buffer(screen_vertex_data)
        self._vao_light = self.ctx.vertex_array(self._prog_light, [
            (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self._vao_blur = self.ctx.vertex_array(self._prog_blur, [
            (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self._vao_mask = self.ctx.vertex_array(self._prog_mask, [
            (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])
        self._vao_draw = self.ctx.vertex_array(self._prog_draw, [
            (screen_vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

    def _create_frame_buffers(self):
        # Frame buffers
        self._tex_bg = self.ctx.texture(self._true_res, components=4)
        self._tex_bg.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fbo_bg = self.ctx.framebuffer([self._tex_bg])

        self._tex_fg = self.ctx.texture(self._true_res, components=4)
        self._tex_fg.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fbo_fg = self.ctx.framebuffer([self._tex_fg])

        # Double buffer for lights
        self._buf_lt = DoubleBuff(self.ctx, self._lightmap_res)

        # Ambient occlussion map
        self._tex_ao = self.ctx.texture(
            self._lightmap_res, components=4, dtype='f2')
        self._tex_ao.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self._fbo_ao = self.ctx.framebuffer([self._tex_ao])


        self._buf_lt._tex1.repeat_x = False
        self._buf_lt._tex1.repeat_y = False
        self._buf_lt._tex2.repeat_x = False
        self._buf_lt._tex2.repeat_y = False

        self._tex_ao.repeat_x = False
        self._tex_ao.repeat_y = False
        self._tex_bg.repeat_x = False
        self._tex_bg.repeat_y = False 
        self._tex_fg.repeat_x = False
        self._tex_fg.repeat_y = False 

    
    def _create_ssbos(self):
        # Set block indices for the SSBOS in the shader program
        prog_glo = self._prog_light.glo

        blockIndex = glGetUniformBlockIndex(prog_glo, 'hullVSSBO')
        glUniformBlockBinding(prog_glo, blockIndex, 1)

        blockIndex = glGetUniformBlockIndex(prog_glo, 'hullIndSSBO')
        glUniformBlockBinding(prog_glo, blockIndex, 2)

        # Create SSBOs
        self._ssbo_v = self.ctx.buffer(reserve=20*2048)
        self._ssbo_v.bind_to_uniform_block(1)
        self._ssbo_ind = self.ctx.buffer(reserve=20*256)
        self._ssbo_ind.bind_to_uniform_block(2)



    def _get_unbound_objects(self) -> str:
        string = "" 
        if not self._player: string += 'player; '
        if not self._tilemap : string += 'tilemap; '
        if not self._background : string += 'background; '
        if not self._entities_atl : string += 'entities atlas;'

        return string
        
    
    def _render_background_textures_to_fbo(self,fbo:moderngl.Framebuffer,infinite:bool = False,offset = (0,0)):

        """
        Render the background (list of textures) to the Background layer.
    
        """
        scroll = offset[0]
        speed = 1
        for tex in self._background:
            if infinite:
                # Calculate the width of the texture and the number of tiles needed to cover the screen
                texture_width = tex.width
                num_tiles = (self._true_res[0] // texture_width) + 2  # +2 to ensure seamless wrap

                # Loop through enough panels to cover the screen
                for panel in range(-1, num_tiles):
                    x_pos = int(panel * texture_width - (scroll * 0.05 * speed) % texture_width)
                    self._render_tex_to_fbo(
                        tex,
                        fbo,
                        dest=pygame.Rect(x_pos, int(-min(0, offset[1]) * 0.05), texture_width, self._true_res[1]),
                        source=pygame.Rect(0, 0, texture_width, tex.height)
                    )
            else: 
                for panels in range(-1,2):
                    self._render_tex_to_fbo(
                        tex,fbo,
                        dest= pygame.Rect(int(panels*self._true_res[0]-scroll * 0.05 * speed),int(-min(0,offset[1]) * 0.05),self._true_res[0],self._true_res[1]),
                        source= pygame.Rect(0,0,tex.width,tex.height)   
                    )
                speed += 1 
            
    
    def _render_player(self,fbo:moderngl.Framebuffer,offset):
        entities_atl = self._entities_atl
        texture_atl_pos = ENTITIES_ATLAS_POSITIONS[self._player.type][self._player.holding_gun][self._player.state]
        self._render_tex_to_fbo(
            entities_atl,fbo,
            dest=pygame.Rect(self._player.pos[0] - offset[0] ,self._player.pos[1] - offset[1],16,16),
            source = pygame.Rect(texture_atl_pos[0]+16 * self._player._cur_animation.curr_frame(),texture_atl_pos[1],16,16),
            flip =self._player.flip
        
        )
        if self._player._cur_weapon_node:
            # TODO: render the player's weapon here 
            pass 

    def _render_hud(self,fbo:moderngl.Framebuffer) -> None: 
        ui_items_atlas = self._hud._ui_items_atlas
        # TODO: the vertex buffer for the stamina bar and the health bar is fixed to two slots of info. 
        # create the vertex buffer before hand for further optimization. 

        vertices_list = []
        texture_coords_list = []

        opaque_vertices_list = []
        opaque_texture_coords_list = []

        #rare_items_vertices_list = []
        #rare_items_texture_coords_list = []

        for ui_name in self._hud._bars:
            texture_coords = self._hud._tex_dict[ui_name]
            vertices = self._create_hud_element_vertices(self._hud._bars[ui_name],fbo)

            vertices_list.append(vertices)
            texture_coords_list.append(texture_coords)
        
        opacity =255 

        for inventory in self._hud._inven_list:
            if inventory._name.endswith('item'):
                if inventory._expandable:
                    if inventory.cur_opacity > 0 :
                        opacity = inventory.cur_opacity
                        background_texture_coords = self._hud._tex_dict["background"]
                        background_vertices  = self._hud._vertices_dict[f"{inventory.name}_{inventory.ind}_background"][inventory.done_open]
                        opaque_vertices_list.append(background_vertices)
                        opaque_texture_coords_list.append(background_texture_coords)

                        for i in range(inventory._rows):
                            for j in range(inventory._columns):
                                cell = inventory._cells[i][j]
                                texture_coords = self._hud._tex_dict[f"{inventory._name}_slot"][cell._hovered]
                                vertices = self._hud._vertices_dict[f"{inventory._name}_{inventory._ind}"][i*inventory._columns + j][cell._hovered]
                                opaque_vertices_list.append(vertices)
                                opaque_texture_coords_list.append(texture_coords)
                                
                                if cell._item: 
                                    texture_coords = self._hud._item_tex_dict[cell._item.name]
                                    vertices = self._hud._item_vertices_dict[f"{inventory._name}_{inventory._ind}"][i*inventory._columns + j][cell._hovered]
                                    
                                    opaque_vertices_list.append(vertices)
                                    opaque_texture_coords_list.append(texture_coords)
                                    
                                    number = cell._item.count
                                    self._create_vertex_texture_coords_for_num(inventory,i,j,number,opaque_vertices_list,opaque_texture_coords_list) 
                                 

                else: 
                    # if the inventory is not expandable, then it is always open, 
                    for i in range(inventory._rows):
                        for j in range(inventory._columns):
                                cell = inventory._cells[i][j]
                                texture_coords = self._hud._tex_dict[f"{inventory._name}_slot"][cell._hovered]
                                vertices = self._hud._vertices_dict[f"{inventory._name}_{inventory._ind}"][i*inventory._columns + j][cell._hovered]
                                vertices_list.append(vertices)
                                texture_coords_list.append(texture_coords)
                                if cell._item: 
                                    texture_coords = self._hud._item_tex_dict[cell._item.name]
                                    vertices = self._hud._item_vertices_dict[f"{inventory._name}_{inventory._ind}"][i*inventory._columns + j][cell._hovered]

                                    # testing the rare effect 
                                    #rare_items_vertices_list.append(vertices)
                                    #rare_items_texture_coords_list.append(texture_coords)
                                    
                                    vertices_list.append(vertices)
                                    texture_coords_list.append(texture_coords)
                                    
                                    number = cell._item.count
                                    self._create_vertex_texture_coords_for_num(inventory,i,j,number,vertices_list,texture_coords_list)
                                    
            else:
                if inventory.cur_opacity > 0 :
                    current = inventory._weapons_list.head 
                    while current: 

                        texture_coords = self._hud._tex_dict[f"{inventory.name}_slot"][current._hovered]
                        vertices = self._hud._vertices_dict[f"{inventory.name}_{inventory._ind}"][current._cell_ind][current._hovered]
                        opaque_texture_coords_list.append(texture_coords)
                        opaque_vertices_list.append(vertices)
                        
                        if current._item:
                            weapon_texture_coords = self._hud._item_tex_dict[current._item.name]
                            weapon_vertices = self._hud._item_vertices_dict[f"{inventory.name}_{inventory._ind}"][current._cell_ind][current._hovered]
                            opaque_vertices_list.append(weapon_vertices)
                            opaque_texture_coords_list.append(weapon_texture_coords)
                        current = current.next 

               
        if self._hud.cursor.item:
            item_texture_coord = self._hud._item_tex_dict[self._hud.cursor.item.name]
            item_vertices = self._create_vertices_for_item(fbo)
            
            vertices_list.append(item_vertices)
            texture_coords_list.append(item_texture_coord)
            
         
        
        # cursor rendering 
        cursor_texture_coord = self._hud._tex_dict["cursor"][self._hud.cursor.state]
        cursor_vertices = self._create_hud_element_vertices(self._hud.cursor,fbo)

        vertices_list.append(cursor_vertices)
        texture_coords_list.append(cursor_texture_coord)

        if opaque_vertices_list:
            vertices_array = np.concatenate(opaque_vertices_list,axis= 0)
            texture_coords_array = np.concatenate(opaque_texture_coords_list,axis= 0)

            buffer_data = np.column_stack((vertices_array,texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)

            self._render_ui_elements(vbo,fbo,ui_items_atlas,opacity)
        if vertices_list:
            vertices_array = np.concatenate(vertices_list,axis= 0)
            texture_coords_array = np.concatenate(texture_coords_list,axis= 0)

            buffer_data = np.column_stack((vertices_array,texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)

            self._render_ui_elements(vbo,fbo,ui_items_atlas)
        
        """
        if rare_items_vertices_list:
            rare_vertices_array = np.concatenate(rare_items_vertices_list,axis= 0)
            rare_texture_coords_array = np.concatenate(rare_items_texture_coords_list,axis= 0)
            buffer_data = np.column_stack((rare_vertices_array,rare_texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)

            self._render_rare_items(vbo,fbo,ui_items_atlas)
        """    
    def _render_rare_items(self,vbo:moderngl.Context.buffer,fbo:moderngl.Framebuffer,ui_items_atlas:moderngl.Texture)-> None:
        vao = self.ctx.vertex_array(self._prog_shimmer, [(vbo,'2f 2f','vertexPos', 'vertexTexCoord')])
        
        self._time = time.time() % 1000
        self._prog_shimmer['time'].value = self._time

        ui_items_atlas.use()
        fbo.use()
        vao.render()
        vbo.release()
        vao.release()

    def _create_vertex_texture_coords_for_num(self,inventory,i,j,number,vertices_list,texture_coords_list) -> None: 
        str_num = str(number)
        num_length = len(str_num)
        for pos_ind, digit in enumerate(str_num):
            texture_coords = self._hud._text_tex_dict[int(digit)]
            vertices = self._create_vertices_for_num(pos_ind,num_length,i,j,inventory)


            vertices_list.append(vertices)
            texture_coords_list.append(texture_coords)
            
    def _create_vertices_for_num(self,pos_ind:int,num_length:int,i:int,j:int,inventory) -> np.array: 
        topleft = inventory.topleft 
        cell_dim = inventory._cell_dim 
        space_between_cells = inventory._space_between_cells

        x = 2. * (topleft[0]+ cell_dim[0] - (num_length-pos_ind)*cell_dim[0]//5 + j * cell_dim[0] + ((space_between_cells * (j)) if j >0 else 0)) / self._true_res[0] -1.
        y = 1. - 2. * (topleft[1] + cell_dim[1]*3//4 + i * cell_dim[1] + ((space_between_cells * (i)) if i >0 else 0)) / self._true_res[1]
        w = 2. * (cell_dim[0]//5)/ self._true_res[0]
        h = 2. * (cell_dim[1]//4) / self._true_res[1]

        return np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)

        


    def _render_ui_elements(self,vbo:moderngl.Context.buffer,fbo:moderngl.Framebuffer,ui_items_atlas: moderngl.Texture,opacity = None)-> None:
        vao = self.ctx.vertex_array(self._prog_draw, [(vbo,'2f 2f','vertexPos', 'vertexTexCoord')])

        if opacity:
            self.set_alpha_value_draw_shader(opacity/255)

        ui_items_atlas.use()
        fbo.use()
        vao.render()
        vbo.release()
        vao.release()

        if opacity:
            self.set_alpha_value_draw_shader(1.)

    def _create_vertices_for_item(self,fbo:moderngl.Framebuffer):
        topleft = (self._hud.cursor.topleft[0]- 31//2 ,\
                   self._hud.cursor.topleft[1]- 12//2)
        width,height = 31, 12 
        x = 2. * (topleft[0]) / fbo.width -1.
        y = 1. - 2. * (topleft[1] ) /fbo.height 
        w = 2. * width /fbo.width
        h = 2. * height /fbo.height
        vertices = np.array([(x,y),(x+w,y),(x,y-h),
                             (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)
        
        return vertices


    def _create_hud_element_vertices(self,element,fbo:moderngl.Framebuffer) -> np.array:
        
        topleft = element.topleft 
        ui_width,ui_height = element.size[0],element.size[1] 

        x = 2. * (topleft[0]) / fbo.width -1.
        y = 1. - 2. * (topleft[1] ) /fbo.height 
        w = 2. * ui_width /fbo.width
        h = 2. * ui_height /fbo.height
        vertices = np.array([(x,y),(x+w,y),(x,y-h),
                             (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)
        
        return vertices
       
    
    def _render_tilemap(self, fbo: moderngl.Framebuffer, offset):
        # fetch the ambient light colorvalue from the tilemap 
        if isinstance(self._tilemap._ambient_node_ptr,interpolatedLightNode):
            self.set_ambient(self._tilemap._ambient_node_ptr.get_interpolated_RGBA(self._player.pos[0]))
        else:
            self.set_ambient(*self._tilemap._ambient_node_ptr.colorValue) 


        # fetch the background framebuffer
        fbo_w,fbo_h = fbo.size
        
        # setup vertex data and texture coordinate lists 
        vertices_list = []
        texture_coords_list = []


        # create a vertex buffer that contains the vertex and fragment coordinates for the tiles within the screen  
        for x in range(offset[0] // self._tilemap.tile_size- 1, (offset[0] + self._true_res[0]) // self._tilemap.tile_size+ 1):
            for y in range(offset[1] // self._tilemap.tile_size- 1, (offset[1] + self._true_res[1]) // self._tilemap.tile_size+1):
                coor = (x,y) 

                # add non-physical tiles first 
                for i,dict in enumerate(self._tilemap.non_physical_tiles): 
                    if coor in dict: 
                        tile_info = self._tilemap.non_physical_tiles[i][coor]
                        

                        # Get texture coords for the tile 
                        texture_coords = self._tilemap._texcoord_dict[(tile_info.type,tile_info.variant)]

                        # Get the tile vertex coordinates 
                        vertices = self._create_tile_vertices(tile_info,offset,fbo_w,fbo_h)
                        vertices_list.append(vertices)
                        texture_coords_list.append(texture_coords)                                         

                # add physica tiles 
                if coor in self._tilemap.physical_tiles:  

                    # the tile info named tuple is always the first element of the list. 
                    tile_info_list = self._tilemap.physical_tiles[coor]
                    tile_info  = tile_info_list[0]
                        
                    
                    # Get texture coordinates for the tile 
                    texture_coords = self._tilemap._texcoord_dict[(tile_info.type,tile_info.variant)]

                    # Create the vertex data (tile positions and texture coordinates)
                    vertices = self._create_tile_vertices(tile_info,offset,fbo_w,fbo_h)
                    vertices_list.append(vertices)
                    texture_coords_list.append(texture_coords)
        
        # if there is anything to render 
        if vertices_list:
            
            # Flatten the lists into single arrays
            vertices_array = np.concatenate(vertices_list, axis=0)
            texture_coords_array = np.concatenate(texture_coords_list, axis=0)

            # Interleave vertices and texture coordinates
            buffer_data = np.column_stack((vertices_array, texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)
            # Render all visible tiles in one batch
            self._render_tiles(vbo,fbo)


   
    def _create_tile_vertices(self, tile_info:TileInfo ,offset, fbo_w,fbo_h):
        # Calculate screen-space position and texture coordinates for a tile
        tile_pos = tile_info.tile_pos

        x = 2. * (tile_pos[0] * 16 -offset[0] )/ fbo_w- 1.
        y = 1. - 2. * (tile_pos[1] * 16 - offset[1])/ fbo_h
        w = 2. * 16 / fbo_w
        h = 2. * 16 /fbo_h 
        vertices = np.array([(x, y), (x + w, y), (x, y - h),
                            (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)
        
        return vertices

    def _render_tiles(self, vbo,fbo ):
        # Render the entire batch of tiles with a single draw call
        
        vao = self.ctx.vertex_array(self._prog_draw, [(vbo, '2f 2f', 'vertexPos', 'vertexTexCoord')])
        

        self._tilemap.texture_atlas.use()
        fbo.use()
        vao.render()
        vbo.release()
        vao.release()

    def _point_to_uv(self, p: tuple[float, float]):
        return [p[0]/self._true_res[0], 1 - (p[1]/self._true_res[1])]

    def _get_fbo(self, Layer_: Layer_):
        if Layer_ == Layer_.BACKGROUND:
            return self._fbo_bg
        elif Layer_ == Layer_.FOREGROUND:
            return self._fbo_fg
        return None

    def _get_tex(self, Layer_: Layer_):
        if Layer_ == Layer_.BACKGROUND:
            return self._tex_bg
        elif Layer_ == Layer_.FOREGROUND:
            return self._tex_fg
        return None

    def _render_tex_to_fbo(self, tex: moderngl.Texture, fbo: moderngl.Framebuffer, dest: pygame.Rect, source: pygame.Rect,flip:bool = False):
        # Mesh for destination rect on screen
        width, height = fbo.size
        x = 2. * dest.x / width - 1.
        y = 1. - 2. * dest.y / height
        w = 2. * dest.w / width
        h = 2. * dest.h / height
        vertices = np.array([(x, y), (x + w, y), (x, y - h),
                            (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)

        # Mesh for source within the texture
        x = source.x / tex.size[0]
        y = source.y / tex.size[1]
        w = source.w / tex.size[0]
        h = source.h / tex.size[1]

        if flip: 
            p1 = (x + w, y + h)  # Top-right becomes top-left
            p2 = (x, y + h)      # Top-left becomes top-right
            p3 = (x + w, y)      # Bottom-right becomes bottom-left
            p4 = (x, y)          # Bottom-left becomes bottom-right
        else: 
                
            p1 = (x, y + h) 
            p2 = (x + w, y + h) 
            p3 = (x, y) 
            p4 = (x + w, y) 
        tex_coords = np.array([p1, p2, p3,
                               p3, p2, p4], dtype=np.float32)

        # Create VBO and VAO
        buffer_data = np.hstack([vertices, tex_coords])

        vbo = self.ctx.buffer(buffer_data)
        vao = self.ctx.vertex_array(self._prog_draw, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Use buffers and render
        tex.use()
        fbo.use()
        vao.render()

        # Free vertex data
        vbo.release()
        vao.release()

    def _send_hull_data(self,offset):
        # Lists with hull vertices and indices
        vertices = []
        indices = []

        for hull in self.hulls:
            if not hull.enabled:
                continue
            vertices_buffer = [ ]

            #the vertices of the hulls are adjusted by the offset, then added to the list. 

            for vertice in hull.vertices:
                vertices_buffer.append((int(vertice[0]- offset[0]), int(vertice[1]-offset[1])))
            vertices += vertices_buffer
            indices.append(len(vertices))

        # Store hull vertex data in SSBO
        vertices = [self._point_to_uv(v) for v in vertices]
        data_v = np.array(vertices, dtype=np.float32).flatten().tobytes()
        self._ssbo_v.write(data_v)

        # Store hull vertex indices in SSBO
        data_ind = np.array(indices, dtype=np.int32).flatten().tobytes()
        self._ssbo_ind.write(data_ind)

    def _render_to_buf_lt(self,offset):
        # Disable alpha blending to render lights
        range = self._tilemap._ambient_node_ptr.range

        self.ctx.disable(moderngl.BLEND)
        for light in self.lights.copy():
            # Skip light if disabled
            if light.popped:
                self.lights.remove(light)
                continue
            if light.illuminator and light.illuminator.dead:
                self.lights.remove(light)
                continue 
            if math.dist(light.position,offset) > light.radius + self._diagonal:
                continue
            
            if not light.illuminator and (light.position[0] < range[0] or light.position[0] > range[1]):
                #decrease power of light 
                dec = light.power/10
                light.cur_power = max(0.0,light.cur_power - dec)
            else: 
                inc = light.power/10
                light.cur_power = min(light.power, light.cur_power + inc)

                
            if light.life == 0:
                self.lights.remove(light)
                continue
            elif light.life != -1 :
                light.life -= 1
            if not light.enabled:
                continue

            # Use light double buffers
            self._buf_lt.tex.use()
            self._buf_lt.fbo.use()
            if light.radius_decay: 
                light.radius = max(1,light.radius * (light.life/light.maxlife))

            if light.illuminator: 
                
                light.cur_power = max(0,light.power * (light.life/light.maxlife))
                light.position = (int(light.illuminator.center[0]) , int(light.illuminator.center[1]))    
                
            elif light.life > 0: 
                if light.maxlife-1 == light.life: 
                    light.position = (int(light.position[0]) , int(light.position[1]))
                
             


            #the light position is offseted, then passed to the shader.

            # Send light uniforms
            self._prog_light['lightPos'] = self._point_to_uv((int(light.position[0]-offset[0] ),int(light.position[1]-offset[1] )))
            self._prog_light['lightCol'] = light._color
            self._prog_light['lightPower'] = light.cur_power
            self._prog_light['radius'] = light.radius
            self._prog_light['castShadows'] = light.cast_shadows
            self._prog_light['native_width'] = self._true_res[0]
            self._prog_light['native_height'] = self._true_res[1]

            # Send number of hulls
            self._prog_light['numHulls'] = len(self.hulls)

            # Render onto lightmap
            self._vao_light.render()

            # Flip double buffer
            self._buf_lt.flip()

        # Re-enable alpha blending
        self.ctx.enable(moderngl.BLEND)

    def _render_aomap(self):
        # Use aomap FBO and light buffer texture
        self._fbo_ao.use()
        self._buf_lt.tex.use()

        self._prog_blur['blurRadius'] = self.shadow_blur_radius
        self._vao_blur.render()


    def _render_background_layer(self,offset):
        self.ctx.screen.use()
        self._tex_bg.use()

        self._tex_ao.use(1)

        # calculate lowerBound and upper bound values to pass to shader 
      
       
        self._prog_mask['lightmap'].value = 1
        self._prog_mask['ambient'].value = self._ambient

        #self._prog_mask['range'].value = ((range[0] - offset[0])/self._true_res[0],(range[1] - offset[0])/self._true_res[0])
        
        self._vao_mask.render()

    def _render_foreground(self):
        self.ctx.screen.use()
        self._tex_fg.use()
        self._vao_draw.render()


    def set_offset_value_draw_shader(self,offset : tuple[float,float]) -> None:
        """
        set the offset value for the draw shader. 


        """
        pass 



    def set_alpha_value_draw_shader(self,alpha_value : float) -> None:
        """
        set the alpha value uniform for the draw shader.        
        
        """
        assert  0<= alpha_value <=1

        self._prog_draw['u_alpha'].value = alpha_value



    def release_objects(self):
        self._prog_light.release()
        self._prog_blur.release()
        self._prog_mask.release()
        self._vao_light.release()
        self._prog_draw.release()
        self._tex_bg.release()
        self._fbo_bg.release()
        self._tex_fg.release()
        self._fbo_fg.release()
        self._buf_lt.release()
        self._tex_ao.release()
        self._fbo_ao.release()
        

        self._ssbo_v.release()
        self._ssbo_ind.release()

    



    def set_filter(self, Layer_: Layer_, filter) -> None:
        """
        Set the filter for a specific Layer_'s texture.

        Args:
            Layer_ (Layer_): The Layer_ to apply the filter to.
            filter (tuple[Constant, Constant]): The filter to apply to the texture, can be `NEAREST` or `LINEAR`.
        """
        self._get_tex(Layer_).filter = filter


    def set_aomap_filter(self, filter) -> None:
        """
        Set the aomap's filter.

        Args:
            filter (tuple[Constant, Constant]): The filter to apply to the texture, can be `NEAREST` or `LINEAR`.
        """
        self._tex_ao.filter = filter

    def set_ambient(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255) -> None:
        """
        Set the ambient light color.

        Args:
            R (int or tuple[int]): Red component value or tuple containing RGB or RGBA values (0-255).
            G (int): Green component value (0-255).
            B (int): Blue component value (0-255).
            A (int): Alpha component value (0-255).
        """
        self._ambient = normalize_color_arguments(R, G, B, A)

    
    def get_native_res(self) -> tuple[int,int]:
        """
        Get the native resolution.
        
        Returns: 
            tuple[int,int] 

        """
        return self._true_res 


    def get_ambient(self) -> tuple[int, int, int, int]:
        """
        Get the ambient light color.

        Returns:
            tuple[int, int, int, int]: Ambient light color in 0-255 scale (R, G, B, A).
        """
        return denormalize_color(self._ambient)

    def blit_texture(self, tex: moderngl.Texture, Layer_: Layer_, dest: pygame.Rect, source: pygame.Rect):
        """
        Blit a texture onto a specified Layer_'s framebuffer.

        Args:
            tex (moderngl.Texture): Texture to blit.
            Layer_ (Layer_): Layer_ to blit the texture onto.
            dest (pygame.Rect): Destination rectangle.
            source (pygame.Rect): Source rectangle from the texture.
        """

        # Create a framebuffer with the texture
        fb = self.ctx.framebuffer([tex])

        # Select destination framebuffer correcponding to Layer_
        fbo = self._get_fbo(Layer_)

        # Blit texture onto destination
        glBlitNamedFramebuffer(fb.glo, fbo.glo, source.x, source.y, source.w, source.h,
                               dest.x, dest.y, dest.w, dest.h, GL_COLOR_BUFFER_BIT, GL_NEAREST)

    def render_texture(self, tex: moderngl.Texture, layer: Layer_, dest: pygame.Rect, source: pygame.Rect,angle:float=0.0,flip : tuple[bool,bool]= (False,False)):
        """
        Render a texture onto a specified Layer_'s framebuffer using the draw shader.

        Args:
            tex (moderngl.Texture): Texture to render.
            Layer_ (Layer_): Layer_ to render the texture onto.
            dest (pygame.Rect): Destination rectangle.
            source (pygame.Rect): Source rectangle from the texture.
            angle (float) : angle to rotate around center in radians 
            flip (tuple[bool,bool]) : values to indicate flip vertically and horizontally 
        """

        # Render texture onto Layer_ with the draw shader
        fbo = self._get_fbo(layer)
        self._render_tex_to_fbo(tex, fbo, dest, source )

    def surface_to_texture(self, sfc: pygame.Surface) -> moderngl.Texture:
        """
        Convert a pygame.Surface to a moderngl.Texture.

        Args:
            sfc (pygame.Surface): Surface to convert.

        Returns:
            moderngl.Texture: Converted texture.
        """

        img_flip = pygame.transform.flip(sfc, False, True)
        img_data = pygame.image.tostring(img_flip, "RGBA")

        tex = self.ctx.texture(sfc.get_size(), components=4, data=img_data)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        return tex

    def load_texture(self, path: str) -> moderngl.Texture:
        """
        Load a texture from a file.

        Args:
            path (str): Path to the texture file.

        Returns:
            moderngl.Texture: Loaded texture.
        """

        img = pygame.image.load(BASE_PATH+ path).convert_alpha()
        return self.surface_to_texture(img)


    def create_outline_texture(self,tex: moderngl.Texture,white :bool= False) ->moderngl.Texture:
        """
        Create a completely white/black texture from a texture with colored bits.

        """

        width,height = tex.size

        texture_data = tex.read()

        image_array = np.frombuffer(texture_data,dtype=np.uint8).reshape((height,width,4))
        
        new_array = np.copy(image_array)
        if white:
            new_array[new_array[:,:,3] >0] = [255,255,255,255]
        else: 
            new_array[new_array[:,:,3] >0] = [0,0,0,255]

        new_tex = self.ctx.texture((width,height),4,new_array.tobytes())

        return new_tex
       

    def clear(self, R: (int | tuple[int]) = 0, G: int = 0, B: int = 0, A: int = 255):
        """
        Clear the background with a color.

        Args:
            R (int or tuple[int]): Red component value or tuple containing RGB or RGBA values (0-255).
            G (int): Green component value (0-255).
            B (int): Blue component value (0-255).
            A (int): Alpha component value (0-255).
        """
        R, G, B, A = normalize_color_arguments(R, G, B, A)
        self._fbo_bg.clear(R, G, B, A)
        self._fbo_fg.clear(0, 0, 0, 0)

    def bind_hud(self,hud:HUD) -> None: 
        self._hud = hud 

    def bind_player(self,player:Player) -> None: 
        self._player = player 


    def bind_tilemap(self,tilemap:Tilemap) -> None:
        self._tilemap = tilemap

    def bind_entities_atlas(self,entities_atl:moderngl.Texture) -> None:
        self._entities_atl = entities_atl
    
    def bind_background(self,background:list[moderngl.Texture]) -> None: 
        self._background = background
    
    
    def render_scene_with_lighting(self,offset,screen_shake):
        """
        Render the lighting effects onto the screen.

        Clears intermediate buffers, renders lights onto the double buffer,
        blurs the lightmap for soft shadows, and renders background and foreground.

        This method is responsible for the final rendering of lighting effects onto the screen.
        """

        """
        
        offset parameter is added for adjusting the light positions based on camera movement.
        
        
        """


        # Clear intermediate buffers
        self.ctx.screen.clear(0, 0, 0, 1)
        self._fbo_ao.clear(0, 0, 0, 0)
        self._buf_lt.clear(0, 0, 0, 0)


        render_shake = (int((offset[0] -screen_shake[0])),int((offset[1] -screen_shake[1])))


        """
        
        position of 'hulls' or shadow objects, and the lights  are  offsetted.

        """


        # Send hull data to SSBOs
        self._send_hull_data(render_shake)

        # Render lights onto double buffer
        self._render_to_buf_lt(render_shake)

        # Blur lightmap for soft shadows and render onto aomap
        self._render_aomap()

        # Render background masked with the lightmap
        self._render_background_layer(offset)

        # Render foreground onto screen
        self._render_foreground()

        
   
    def make_shader(self, vertex_src: str, fragment_src: str) -> Shader:
        """
        Creates a shader program using the provided vertex and fragment shader source code.

        Parameters:
        - vertex_src (str): A string containing the source code for the vertex shader.
        - fragment_src (str): A string containing the source code for the fragment shader.

        Returns:
        - A Shader object representing the compiled shader program.

        Note: If you want to load the shader source code from a file path, consider using the
        'load_shader_from_path' method instead.
        """
        prog = self.ctx.program(vertex_shader=vertex_src,
                                fragment_shader=fragment_src)
        shader = Shader(prog)
        return shader

    def load_shader_from_path(self, vertex_path: str, fragment_path: str) -> Shader:
        """
        Loads shader source code from specified file paths and creates a shader program.

        Parameters:
        - vertex_path (str): File path to the vertex shader source code.
        - fragment_path (str): File path to the fragment shader source code.

        Returns:
        - A Shader object representing the compiled shader program.
        """
        with open(vertex_path) as f:
            vertex_src = f.read()
        with open(fragment_path) as f:
            fragment_src = f.read()

        return self.make_shader(vertex_src, fragment_src)

    def render_background_only_to_fbo(self,background:list[moderngl.Texture],offset = (0,0),infinite:bool = False):
        fbo = self._get_fbo(Layer_.BACKGROUND)
        self._render_background_textures_to_fbo(fbo,background,infinite= infinite,offset=offset)


    def render_tile_panel(self,text_atl: moderngl.Texture,tile_panel:TilePanel):
        """
        Render the tile panel onto the foreground buffer.

        Meant to be used with the editor only. 
        
        """
        fbo = self._get_fbo(Layer_.FOREGROUND)
        categories_panel:TileCategories = tile_panel.categories
        categories_panel_scroll = tile_panel.category_panel_scroll
        topleft = categories_panel.topleft

        fbo_w,fbo_h = fbo.size 
        atl_size = text_atl.size 
        vertices_list = []
        texture_coords_list = []

        curr = categories_panel.head 
        category_stack_offset = 0
        while curr:
            character_length_offset = 0
            for i,char in enumerate(curr.data):
                text_dim,text_atlas_pos,ind = self._get_text_dim_and_atlas_pos(char)


                texture_coords = self._get_texture_coords_for_char(text_dim,text_atlas_pos,ind,atl_size)
                vertices = self._create_char_vertices(topleft,categories_panel_scroll,character_length_offset, category_stack_offset,
                                                     text_dim,fbo_w,fbo_h)
                
                vertices_list.append(vertices)
                texture_coords_list.append(texture_coords)
                character_length_offset += text_dim[0]
            category_stack_offset += curr.height + 1 
            curr = curr.next

        if vertices_list:
            vertices_array = np.concatenate(vertices_list,axis=0)
            texture_coords_array = np.concatenate(texture_coords_list,axis = 0)
            
            buffer_data = np.column_stack((vertices_array,texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)

            self._render_categories(vbo,fbo,text_atl)

    def _render_categories(self,vbo,fbo,alphabet_atl):

        vao = self.ctx.vertex_array(self._prog_draw, [(vbo, '2f 2f', 'vertexPos', 'vertexTexCoord')])
        alphabet_atl.use()
        fbo.use()
        vao.render()
        vbo.release()
        vao.release()            

    def _get_text_dim_and_atlas_pos(self,char:str):
        ord_val = ord(char)
        if 48 <= ord_val <= 57:
            ind = ord_val - 48 
            text_dim = TEXT_DIMENSIONS['NUMBERS']
            bottom_left = (0,5)
        elif 65 <= ord_val <= 90: 
            ind = ord_val - 65 
            text_dim = TEXT_DIMENSIONS['CAPITAL']
            bottom_left = TEXT_ATLAS_POSITIONS['CAPITAL']
        elif 97 <= ord_val <= 122:
            ind = ord_val - 97
            text_dim = TEXT_DIMENSIONS['LOWER']
            bottom_left = TEXT_ATLAS_POSITIONS['LOWER']
        else: 
            ind = 0
            text_dim = TEXT_DIMENSIONS["UNDERSCORE"]
            bottom_left = TEXT_ATLAS_POSITIONS['UNDERSCORE']

        return text_dim,bottom_left,ind
       


    def _create_char_vertices(self,topleft, offset,char_len_offset,cat_stack_offset,text_dim,fbo_w,fbo_h):


        x = 2. * (topleft[0] +char_len_offset)/ fbo_w- 1.
        y = 1. - 2. * (topleft[1] - offset + cat_stack_offset)/ fbo_h
        w = 2. * text_dim[0] / fbo_w
        h = 2. * text_dim[1] /fbo_h 
        vertices = np.array([(x, y), (x + w, y), (x, y - h),
                            (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)
        
        return vertices


    def _get_texture_coords_for_char(self,text_dim,atl_pos,ind,atl_size):
        
        x = (atl_pos[0] + text_dim[0] * ind ) / atl_size[0] 
        y = (atl_pos[1] +text_dim[1]-1) / atl_size[0] 

        w = text_dim[0] / atl_size[0]
        h = text_dim[1] / atl_size[1]
        
        p1 = (x, y + h) 
        p2 = (x + w, y + h) 
        p3 = (x, y) 
        p4 = (x + w, y) 
        tex_coords = np.array([p1, p2, p3,
                            p3, p2, p4], dtype=np.float32)
    
        return tex_coords
    


    def render_rectangles(self, offset):
        # Create a buffer surface for drawing all rectangles at once
        buffer_surf = pygame.Surface(self._true_res).convert_alpha()
        buffer_surf.fill((0, 0, 0, 0))

        # Iterate over rectangles
        for rectangle in self._tilemap._rectangles:
            # Rectangle properties
            rect_x, rect_y, rect_x2, rect_y2 = rectangle
            rect_w = rect_x2 - rect_x
            rect_h = rect_y2 - rect_y


            # Calculate screen position relative to the offset
            screen_x = rect_x - offset[0]
            screen_y = rect_y - offset[1]

            # Check if the rectangle is within the visible screen
            if 0 <= screen_x < self._true_res[0] and 0 <= screen_y < self._true_res[1]:
                # Draw the rectangle directly onto the buffer surface
                pygame.draw.rect(
                    buffer_surf,
                    (244, 244, 244, 244),  # Color with alpha
                    pygame.Rect(screen_x, screen_y, rect_w, rect_h),  # Position and size
                    width=1,  # Line width
                )

        # Convert the buffer surface to a texture
        tex = self.surface_to_texture(buffer_surf)

        # Render the texture
        self.render_texture(
            tex,
            Layer_.FOREGROUND,
            dest=pygame.Rect(0, 0, tex.width, tex.height),
            source=pygame.Rect(0, 0, tex.width, tex.height),
        )

        # Release the texture
        tex.release()

    def _render_particles(self,fbo,camera_scroll):
        particle_system = ParticleSystem.get_instance()
        
        vertices_list = []
        texture_coords_list = []

        for particle in list(particle_system._active_animation_particles):
            cur_frame = particle.animation.curr_frame()
            animationData = PARTICLE_ATLAS_POSITIONS_AND_SIZES[particle.type]

            vertices = self._create_animation_particle_vertices(particle.pos,animationData[1],camera_scroll,fbo.width,fbo.height)
            texture_coords = particle_system._tex_dict[(particle.type,cur_frame)]

            vertices_list.append(vertices)
            texture_coords_list.append(texture_coords)

        if vertices_list: 
            vertices_array = np.concatenate(vertices_list,axis = 0)
            texture_coords_array = np.concatenate(texture_coords_list,axis = 0)

            buffer_data = np.column_stack((vertices_array,texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)

            self._render_animated_particles(vbo,fbo,particle_system._texture_atl)
        """
        for particle in list(particle_system._active_animation_particles):

            cur_frame = particle.animation.curr_frame()
            atlas_pos,size = PARTICLE_ATLAS_POSITIONS_AND_SIZES[particle.type]
            self.render_texture(
                particle_system._texture_atl,Layer_.BACKGROUND,
                dest = pygame.Rect(particle.pos[0]-size[0]//2-camera_scroll[0],particle.pos[1]-size[1]//2-camera_scroll[1],size[0],size[1]),
                source = pygame.Rect(atlas_pos[0]+size[0]*cur_frame,atlas_pos[1],size[0],size[1])
            )
        """
        for particle in list(particle_system._active_collide_particles):
            buffer_surf = particle._buffer_surf
            tex = self.surface_to_texture(buffer_surf)
            self.render_texture(tex,Layer_.BACKGROUND,
                dest = pygame.Rect(particle._pos[0]-camera_scroll[0],particle._pos[1]-camera_scroll[1],tex.width,tex.height),
                source = pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()
        
    
    def _create_animation_particle_vertices(self,pos:tuple[int,int],size: tuple[int,int],camera_scroll : tuple[int,int],fbo_w,fbo_h):
        x = 2. * (pos[0]  - size[0]//2 -camera_scroll[0]) / fbo_w -1.
        y = 1. - 2. * (pos[1] - size[1]//2 -camera_scroll[1]) /fbo_h 
        w = 2. * size[0] /fbo_w
        h = 2. * size[1] /fbo_h
        vertices = np.array([(x,y),(x+w,y),(x,y-h),
                             (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)
        
        return vertices

    def _render_animated_particles(self,vbo:moderngl.Context.buffer,fbo:moderngl.Framebuffer,texture_atl:moderngl.Texture):
        
        vao = self.ctx.vertex_array(self._prog_draw,[(vbo,'2f 2f', 'vertexPos','vertexTexCoord')])

        texture_atl.use()
        fbo.use()
        vao.render()
        vbo.release()
        vao.release()
    

    def render_background_scene_to_fbo(self,offset = (0,0),infinite:bool = False)-> None :
        """
        Render to the Background fbo with the parallax background, the tilemap, etc.

        Args: 
            background (list[moderngl.Texture]) : the background textures 
            tilemap (Tilemap) : The tilemap object with the tilemap dictionaries 
            offset (tuple[int,int] = (0,0)) : The camera scroll
            infinite (bool = False) : whether the background should wrap around the screen infinitely.
        
        """

        fbo = self._get_fbo(Layer_.BACKGROUND)
        self._render_background_textures_to_fbo(fbo,offset=offset,infinite=infinite)
        self._render_tilemap(fbo,offset)
        self._render_player(fbo,offset)
        self._render_particles(fbo,offset)

    def render_foreground_scene_to_fbo(self):
        """
        Render to the Foreground fbo with the  GUI, etc. 
        
        """
        fbo = self._get_fbo(Layer_.FOREGROUND)
        self._render_hud(fbo)

    def render_texture_with_trans(self,
               tex: moderngl.Texture,
               layer: Layer_,
               position: tuple[float, float] = (0, 0),
               scale: tuple[float, float] | float = (1.0, 1.0),
               angle: float = 0.0,
               flip: tuple[bool, bool] | bool = (False, False),
               section: pygame.Rect | None = None,
               shader: Shader = None) -> None:
        """
        Render a texture onto a layer with optional transformations.

        Parameters:
        - tex (Texture): The texture to render.
        - layer (Layer): The layer to render onto.
        - position (tuple[float, float]): The position (x, y) where the texture will be rendered. Default is (0, 0).
        - scale (tuple[float, float] | float): The scaling factor for the texture. Can be a tuple (x, y) or a scalar. Default is (1.0, 1.0).
        - angle (float): The rotation angle in degrees. Default is 0.0.
        - flip (tuple[bool, bool] | bool): Whether to flip the texture. Can be a tuple (flip x axis, flip y axis) or a boolean (flip x axis). Default is (False, False).
        - section (pygame.Rect | None): The section of the texture to render. If None, the entire texture is rendered. Default is None.
        - shader (Shader): The shader program to use for rendering. If None, a default shader is used. Default is None.

        Returns:
        None

        Note:
        - If scale is a scalar, it will be applied uniformly to both x and y.
        - If flip is a boolean, it will only affect the x axis.
        - If section is None, the entire texture is used.
        - If section is larger than the texture, the texture is repeated to fill the section.
        - If shader is None, a default shader (_prog_draw) is used.
        """

        # Create section rect if none
        if section == None:
            section = pygame.Rect(0, 0, tex.width, tex.height)

        # Default to draw shader program if none
        if shader == None:
            shader = Shader(self._prog_draw)

        # If the scale is not a tuple but a scalar, convert it into a tuple
        if isinstance(scale, numbers.Number):
            scale = (scale, scale)

        # If flip is not a tuple but a boolean, convert it into a tuple
        if isinstance(flip, bool):
            flip = (flip, False)

        # Get the vertex coordinates of a rectangle that has been rotated,
        # scaled, and translated, in world coordinates
        points = create_rotated_rect(position, section.width,
                                     section.height, scale, angle, flip)

        # Convert to destination coordinates
        dest_width, dest_height = tex.width,tex.height

        points = [to_dest_coords(p, dest_width, dest_height) for p in points]

        # Mesh for destination rect on screen
        p1, p2, p3, p4 = points
        vertex_coords = np.array([p3, p4, p2,
                                  p2, p4, p1], dtype=np.float32)

        # Calculate the texture coordinates
        x = section.x / tex.width
        y = section.y / tex.height
        w = section.width / tex.width
        h = section.height / tex.height

        # Mesh for the section within the texture
        tex_coords = np.array([(x, y + h), (x + w, y + h), (x, y),
                               (x, y), (x + w, y + h), (x + w, y)], dtype=np.float32)

        # Create VBO and VAO
        buffer_data = np.hstack([vertex_coords, tex_coords])

        vbo = self.ctx.buffer(buffer_data)
        vao = self.ctx.vertex_array(shader.program, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Use textures
        tex.use()
        shader.bind_sampler2D_uniforms()


        fbo = self._get_fbo(layer)

        # Set layer as target
        fbo.use()

        # Render
        vao.render()

        # Clear the sampler2D locations
        shader.clear_sampler2D_uniforms()

        # Free vertex data
        vbo.release()
        vao.release()