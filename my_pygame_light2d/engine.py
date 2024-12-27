from importlib import resources
from enum import Enum
import numpy as np
import moderngl
import pygame
import numbers
from OpenGL.GL import glBlitNamedFramebuffer,glViewport, GL_COLOR_BUFFER_BIT, GL_NEAREST, glGetUniformBlockIndex, glUniformBlockBinding
from math import ceil,dist,sqrt,cos,sin,radians,pi
import time
from random import randint

from pygame.math import Vector2 as vec2 
from scripts.layer import Layer_
from scripts.data import PARTICLE_ANIMATION_PIVOTS
from scripts.data import UI_ATLAS_POSITIONS_AND_SIZES, TILE_ATLAS_POSITIONS,\
                                    ENTITIES_ATLAS_POSITIONS,PARTICLE_ATLAS_POSITIONS_AND_SIZES
from scripts.lists import interpolatedLightNode
from scripts.new_particles import ParticleSystem
from scripts.entitiesManager import EntitiesManager
from scripts.resourceManager import ResourceManager
from scripts.new_grass import GrassManager

from my_pygame_light2d.shader import Shader 
from my_pygame_light2d.color import normalize_color_arguments, denormalize_color
from my_pygame_light2d.double_buff import DoubleBuff
from my_pygame_light2d.util import create_rotated_rect,to_dest_coords

BASE_PATH = 'data/images/'

from typing import TYPE_CHECKING

if TYPE_CHECKING: 
    from scripts.new_particles import Spark
    from scripts.new_panel import TilePanel
    from my_pygame_light2d.light import PointLight
    from my_pygame_light2d.hull import Hull
    from scripts.new_entities import Player
    from scripts.new_cursor import Cursor
    from scripts.new_HUD import HUD
    from scripts.new_tilemap import Tilemap
    from scripts.data import TileInfo
    from scripts.lists import TileCategories

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
        # Retrieve context 
        self.ctx = context

        # singleton references 
        self._rm = ResourceManager.get_instance()
        self._em = EntitiesManager.get_instance()
        self._ps = ParticleSystem.get_instance()
        self._gm = GrassManager.get_instance()

        # Initialize  members
        self._true_to_native_ratio = true_to_screen_res_ratio 
        self._screen_res = screen_res
        self._true_res = true_res 

        self._diagonal = sqrt(self._true_res[0] ** 2 + self._true_res[1] ** 2)
        self._lightmap_res = true_res 
        self._ambient = (.25, .25, .25, .25)

        # Initialize buffers for particles 
        #self._fire_instance_buffer = self.ctx.buffer(reserve= self._ps._max_fire_particle_count*2 * 28)


        # Objects that need to be bound to engine before rendering : 
        self._tilemap:"Tilemap" = None
        self._player:"Player"= None
        self._background: list[moderngl.Texture]= None

        # Initialize public members
        self.lights: list["PointLight"] = []
        self.hulls: list["Hull"] = []
        self.shadow_blur_radius: int =5

        
        # Load shaders
        self._load_shaders()

        # Create VAO and VBO
        self._create_screen_vertex_buffers()

        # Create render textures and corresponding FBOs
        self._create_frame_buffers()

        # Create SSBO for hull vertices
        self._create_ssbos()


    def _load_shaders(self)-> None:



        # Read source files

        with open('my_pygame_light2d/fireCompute.glsl',encoding='utf-8') as file:
            fire_compute_shader_src = file.read()
        with open('my_pygame_light2d/vertex_circle.glsl',encoding='utf-8') as file:
            circle_vertex_src = file.read()
        with open('my_pygame_light2d/fragment_circle.glsl',encoding='utf-8') as file:
            circle_fragment_src = file.read()
        with open('my_pygame_light2d/polygon_vertex.glsl',encoding='utf-8') as file:
            polygon_vertex_src= file.read()
        with open('my_pygame_light2d/fragment_polygon.glsl',encoding='utf-8') as file:
            polygon_fragment_src = file.read()

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

        self._prog_polygon_draw = self.ctx.program(vertex_shader=polygon_vertex_src,
                                                   fragment_shader= polygon_fragment_src)

        self._prog_circle_draw = self.ctx.program(vertex_shader=circle_vertex_src,
                                                  fragment_shader=circle_fragment_src)
        self._fire_compute_shader = self.ctx.compute_shader(fire_compute_shader_src)



    def _create_screen_vertex_buffers(self)-> None:
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
        
        """
        self._vao_fire = self.ctx.vertex_array(self._prog_circle_draw,
                                               [
                                                   (self._rm.circle_template[0], '2f', 'in_vert'),
                                                   (self._fire_instance_buffer, '2f 4f 1f/i', 'offset','in_color','size')
                                               ],
                                               self._rm.circle_template[1])
        """

    def _create_frame_buffers(self)->None:
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

    
    def _create_ssbos(self)-> None:
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

        self._ssbo_fp = self.ctx.buffer(self._ps._fire_particle_data.tobytes())
        self._ssbo_fp.bind_to_storage_buffer(0)


    def _render_background_textures_to_fbo(self,fbo:moderngl.Framebuffer,infinite:bool = False,offset = (0,0))-> None:

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
            
    
    def _render_player(self,fbo:moderngl.Framebuffer,interpolation_alpha:float = 0.0,offset = (0,0))-> None:
        weapon = None 
        if self._player.curr_weapon_node and self._player.curr_weapon_node.weapon: 
            weapon = self._player.curr_weapon_node.weapon
        knockback = [0,0] if not weapon else weapon.knockback

        texture_atl_pos = ENTITIES_ATLAS_POSITIONS[self._player.type][self._player.holding_gun][self._player.state]

        interpolate_position = self._player._on_ramp == 0 and self._player.state != "wall_slide" and self._player.state != "slide"
        interpolation_offset = (int(self._player.velocity[0] * interpolation_alpha),int(self._player.velocity[1] * interpolation_alpha)) if interpolate_position else (0,0)
        interpolated_dest_position = (self._player.pos[0] + interpolation_offset[0] + knockback[0]/self._player.knockback_reduction_factor[0] - offset[0],\
                                      self._player.pos[1] + interpolation_offset[1] + knockback[1]/self._player.knockback_reduction_factor[1] - offset[1])
        self._render_tex_to_fbo(
            self._rm.entities_atlas,fbo,
            dest=pygame.Rect(*interpolated_dest_position,self._player.sprite_size[0],self._player.sprite_size[1]),
            source = pygame.Rect(texture_atl_pos[0]+self._player.sprite_size[0]* self._player.cur_animation.curr_frame(),texture_atl_pos[1],self._player.sprite_size[0],self._player.sprite_size[1]),
            flip =self._player.flip
        )

        if weapon:
            
            size = weapon.size
            anchor_offset = (self._player.right_anchor[0] -1,self._player.right_anchor[1]) if weapon.flipped else self._player.left_anchor
            pos = (self._player.pos[0]+interpolation_offset[0]+knockback[0]+anchor_offset[0] - offset[0],\
                    self._player.pos[1] +interpolation_offset[1]+knockback[1] + anchor_offset[1] -offset[1])

            texture_coords = self._rm._in_world_item_texcoords[weapon.name]['holding'] 
            vertices = self._create_rotated_vertices(size,pos,-weapon.angle_opening,weapon.pivot,weapon.flipped)

            buffer_data =  np.column_stack([vertices,texture_coords]).astype(np.float32)

            vbo = self.ctx.buffer(buffer_data)
            vao = self.ctx.vertex_array(self._prog_draw, [(vbo,'2f 2f','vertexPos', 'vertexTexCoord')])

            self._rm.held_wpn_atlas.use()
            fbo.use()
            vao.render()
            vao.release()
            vbo.release()

    # TODO: define the types for pos and rotation angle after cleaning up code and figuring out their types
    
    def _create_rotated_vertices(self, size:tuple[int,int], pos,rotation_angle,pivot:tuple[int,int],flipped:bool)->np.array:
        # step 1: create vertices around the origin. 
        p0 = vec2(-size[0]//2, size[1]//2) # topleft 
        p1 = vec2(size[0]//2 , size[1]//2) # topright 
        p2 = vec2(-size[0]//2 , -size[1]//2) # bottomleft 
        p3 = vec2(size[0]//2 , -size[1]//2) # bottomright  

        
        # step 2: move the vertices by the offset. 
        if flipped:
            flipped_pivot = (size[0]-1-pivot[0],pivot[1])

            offset = (flipped_pivot[0]-size[0]//2,flipped_pivot[1]-size[1]//2)
        else:
            offset = (pivot[0]-size[0]//2, pivot[1]-size[1]//2)

        p0 -= offset
        p1 -= offset
        p2 -= offset
        p3 -= offset
        
        # step 3: do the rotation.
        sign = 1 if rotation_angle> 0 else -1 
        if flipped:
            angle =  (180 - abs(rotation_angle)) * (-1) * sign
        else: 
            angle = rotation_angle
            
        p0.rotate_ip(angle)
        p1.rotate_ip(angle)
        p2.rotate_ip(angle)
        p3.rotate_ip(angle)

        # step 4: translate the points to the world coordinates 

        p0 += pos
        p1 += pos
        p2 += pos
        p3 += pos
        # step 5: map the vertices to screen coords 

        self._map_world_coords_to_screen_coords(p0)        
        self._map_world_coords_to_screen_coords(p1)        
        self._map_world_coords_to_screen_coords(p2)        
        self._map_world_coords_to_screen_coords(p3)        

        # step 6: create the vertices array 
        if flipped: 
            tl = p1 
            tr = p0
            bl = p3
            br = p2 
        else: 
            tl = p0 
            tr = p1
            bl = p2
            br = p3
        return np.array([bl,br,tl,
                         tl,br,tr])



    def _map_world_coords_to_screen_coords(self,vertex)->None:
        vertex[0] = 2. * vertex[0] / self._true_res[0] -1.
        vertex[1] = 1. -2 * vertex[1] / self._true_res[1] 
           


    def _render_hud(self,fbo:moderngl.Framebuffer) -> None: 
        ui_items_atlas = self._rm.ui_item_atlas

        # TODO: the vertex buffer for the stamina bar and the health bar is fixed to two slots of info. 
        # create the vertex buffer before hand for further optimization. 

        vertices_list = []
        texture_coords_list = []

        opaque_vertices_list = []
        opaque_texture_coords_list = []

        
        #rare_items_vertices_list = []
        #rare_items_texture_coords_list = []

        for bar_name in self._hud._bars:
            texture_coords = self._rm._ui_texcoords[bar_name]
            vertices = self._hud._vertices_dict[bar_name]

            vertices_list.append(vertices)
            texture_coords_list.append(texture_coords)
        
        opacity =255 

        for inventory in self._hud._inven_list:
            if inventory.name.endswith('item'):
                if inventory.expandable:
                    if inventory.cur_opacity > 0 :
                        opacity = inventory.cur_opacity
                        background_texture_coords = self._rm._ui_texcoords["background"]
                        background_vertices  = self._hud._vertices_dict[f"{inventory.name}_{inventory.ind}_background"][inventory.done_open]
                        opaque_vertices_list.append(background_vertices)
                        opaque_texture_coords_list.append(background_texture_coords)

                        for i in range(inventory._rows):
                            for j in range(inventory._columns):
                                cell = inventory.cells[i][j]
                                texture_coords = self._rm._ui_texcoords[f"{inventory.name}_slot"][cell.hovered]
                                vertices = self._hud._vertices_dict[f"{inventory.name}_{inventory.ind}"][i*inventory.columns + j][cell.hovered]
                                opaque_vertices_list.append(vertices)
                                opaque_texture_coords_list.append(texture_coords)
                                
                                if cell._item: 
                                    texture_coords = self._rm._item_texcoords[cell.item.name]
                                    vertices = self._hud._item_vertices_dict[f"{inventory.name}_{inventory.ind}"][i*inventory.columns + j][cell.hovered]
                                    opaque_vertices_list.append(vertices)
                                    opaque_texture_coords_list.append(texture_coords)
                                    
                                    number = cell._item.count
                                    self._create_vertex_texture_coords_for_num(inventory,i,j,number,opaque_vertices_list,opaque_texture_coords_list) 
                                 

                else: 
                    # if the inventory is not expandable, then it is always open, 
                    for i in range(inventory.rows):
                        for j in range(inventory.columns):
                                cell = inventory.cells[i][j]
                                texture_coords = self._rm._ui_texcoords[f"{inventory.name}_slot"][cell.hovered]
                                vertices = self._hud._vertices_dict[f"{inventory.name}_{inventory.ind}"][i*inventory.columns + j][cell.hovered]
                                vertices_list.append(vertices)
                                texture_coords_list.append(texture_coords)
                                if cell._item: 
                                    texture_coords = self._rm._item_texcoords[cell.item.name]
                                    vertices = self._hud._item_vertices_dict[f"{inventory.name}_{inventory.ind}"][i*inventory.columns + j][cell.hovered]

                                    # testing the rare effect 
                                    #rare_items_vertices_list.append(vertices)
                                    #rare_items_texture_coords_list.append(texture_coords)
                                    vertices_list.append(vertices)
                                    texture_coords_list.append(texture_coords)
                                    
                                    number = cell.item.count
                                    self._create_vertex_texture_coords_for_num(inventory,i,j,number,vertices_list,texture_coords_list)
                                    
            else:
                if inventory.cur_opacity > 0 :
                    current = inventory.weapons_list.head 
                    while current: 
                        if current.cell_ind == inventory.weapons_list.curr_node.cell_ind:
                            # the weapon panel item rendering is done here
                            

                            item = current.weapon
                            if item is not None: 
                                
                                
                                texture_coords = self._rm._ui_texcoords[f"{inventory.name}_slot"][1]
                                vertices = self._hud._vertices_dict[f"{inventory.name}_{inventory.ind}"][current.cell_ind][1]
                                opaque_texture_coords_list.append(texture_coords)
                                opaque_vertices_list.append(vertices)
                            else: 
                                texture_coords = self._rm._ui_texcoords[f"{inventory.name}_slot"][current.hovered]
                                vertices = self._hud._vertices_dict[f"{inventory.name}_{inventory.ind}"][current.cell_ind][current.hovered]
                                opaque_texture_coords_list.append(texture_coords)
                                opaque_vertices_list.append(vertices)


                        else:
                            texture_coords = self._rm._ui_texcoords[f"{inventory.name}_slot"][current.hovered]
                            vertices = self._hud._vertices_dict[f"{inventory.name}_{inventory.ind}"][current.cell_ind][current.hovered]
                            opaque_texture_coords_list.append(texture_coords)
                            opaque_vertices_list.append(vertices)
                            
                        if current.weapon:
                            weapon_texture_coords = self._rm._item_texcoords[current.weapon.name]
                            weapon_vertices = self._hud._item_vertices_dict[f"{inventory.name}_{inventory.ind}"][current.cell_ind][current.hovered]
                            opaque_vertices_list.append(weapon_vertices)
                            opaque_texture_coords_list.append(weapon_texture_coords)
                        current = current.next 

                if inventory.weapons_list.curr_node.weapon: 
                    left_node,right_node = inventory.weapons_list.curr_node.check_nearest_node_with_item()
                    current_weapon_tex_coords = self._rm._item_texcoords[inventory.weapons_list.curr_node.weapon.name]
                    current_weapon_vertices = self._hud._item_vertices_dict["current_weapon"]

                    vertices_list.append(current_weapon_vertices)
                    texture_coords_list.append(current_weapon_tex_coords)

                current_weapon_display_container = self._rm._ui_texcoords[f"{inventory.name}_slot"][0]
                vertices = self._hud._vertices_dict["current_weapon"][0] 
                
                vertices_list.append(vertices)
                texture_coords_list.append(current_weapon_display_container)
        
        if self._hud.cursor.item:
            if self._hud.cursor.item.type == 'weapon':
                item_texture_coord = self._rm._item_texcoords[self._hud.cursor.item.name]
                item_vertices = self._create_vertices_for_item(fbo,'weapon')
                
                vertices_list.append(item_vertices)
                texture_coords_list.append(item_texture_coord)
            else:
                item_texture_coord = self._rm._item_texcoords[self._hud.cursor.item.name]
                item_vertices = self._create_vertices_for_item(fbo,'item')
                
                vertices_list.append(item_vertices)
                texture_coords_list.append(item_texture_coord)

                number = self._hud.cursor.item.count
                self._create_vertex_texture_coords_for_num_on_cursor(number,vertices_list,texture_coords_list)

                
        
        # cursor rendering 
        cursor_texture_coord = self._rm._ui_texcoords["cursor"][self._hud.cursor.state]
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
    
    def _create_vertex_texture_coords_for_num_on_cursor(self,number,vertices_list,texture_coords_list):
        str_num = str(number)
        num_length = len(str_num)
        for pos_ind, digit in enumerate(str_num):
            texture_coords = self._rm._text_texcoords["NUMBERS"][int(digit)]
            vertices = self._create_vertices_for_num_on_cursor(pos_ind,num_length)


            vertices_list.append(vertices)
            texture_coords_list.append(texture_coords)


    def _create_vertex_texture_coords_for_num(self,inventory,i,j,number,vertices_list,texture_coords_list) -> None: 
        str_num = str(number)
        num_length = len(str_num)
        for pos_ind, digit in enumerate(str_num):
            texture_coords = self._rm._text_texcoords["NUMBERS"][int(digit)]
            vertices = self._create_vertices_for_num(pos_ind,num_length,i,j,inventory)


            vertices_list.append(vertices)
            texture_coords_list.append(texture_coords)
    
    def _create_vertices_for_num_on_cursor(self,pos_ind:int,num_length:int):
        topleft = self._hud.cursor.topleft
        dim = self._hud.cursor.size 
        num_dim = self._hud._text_dim

        x = 2. * (topleft[0] - (num_length-pos_ind)* 5 - 4 ) / self._true_res[0] -1.
        y = 1. - 2. * (topleft[1] + dim[1] //2 - 10  ) / self._true_res[1]
        w = 2. * (num_dim[0])/ self._true_res[0]
        h = 2. * (num_dim[1]) / self._true_res[1]

        return np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)

            
    def _create_vertices_for_num(self,pos_ind:int,num_length:int,i:int,j:int,inventory) -> np.array: 
        topleft = inventory.topleft 
        cell_dim = inventory._cell_dim 
        num_dim = self._hud._text_dim
        space_between_cells = inventory._space_between_cells

        x = 2. * (topleft[0]+ cell_dim[0] - (num_length-pos_ind)* 5 + j * cell_dim[0] + ((space_between_cells * (j)) if j >0 else 0)) / self._true_res[0] -1.
        y = 1. - 2. * (topleft[1] + cell_dim[1] - 7 - 5 + i * cell_dim[1] + ((space_between_cells * (i)) if i >0 else 0)) / self._true_res[1]
        w = 2. * (num_dim[0])/ self._true_res[0]
        h = 2. * (num_dim[1]) / self._true_res[1]

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

    def _create_vertices_for_item(self,fbo:moderngl.Framebuffer,item_type:str):
        if item_type == 'weapon':
            
            topleft = (self._hud.cursor.topleft[0]- 31//2 ,\
                    self._hud.cursor.topleft[1]- 12//2)
            width,height = 31, 12 
            x = 2. * (topleft[0]) / fbo.width -1.
            y = 1. - 2. * (topleft[1] ) /fbo.height 
            w = 2. * width /fbo.width
            h = 2. * height /fbo.height
            vertices = np.array([(x,y),(x+w,y),(x,y-h),
                                (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)
        else: 
            topleft = (self._hud.cursor.topleft[0]- (self._hud._item_inventory_cell_dim[0]-16)//2 ,\
                    self._hud.cursor.topleft[1]- (self._hud._item_inventory_cell_dim[1]-16)//2)
            width,height = 16,16   
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
        y = 1. - 2. * (topleft[1]) /fbo.height 
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


   
    def _create_tile_vertices(self, tile_info:"TileInfo",offset, fbo_w,fbo_h):
        # Calculate screen-space position and texture coordinates for a tile
        tile_pos = tile_info.tile_pos

        x = 2. * (tile_pos[0] * self._tilemap._regular_tile_size-offset[0] )/ fbo_w- 1.
        y = 1. - 2. * (tile_pos[1] * self._tilemap._regular_tile_size- offset[1])/ fbo_h
        w = 2. * 16 / fbo_w
        h = 2. * 16 /fbo_h 
        vertices = np.array([(x, y), (x + w, y), (x, y - h),
                            (x, y - h), (x + w, y), (x + w, y - h)], dtype=np.float32)
        
        return vertices

    def _render_tiles(self, vbo,fbo ):
        # Render the entire batch of tiles with a single draw call
        
        vao = self.ctx.vertex_array(self._prog_draw, [(vbo, '2f 2f', 'vertexPos', 'vertexTexCoord')])
        
        self._rm.tile_atlas.use()
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

    def _render_text(self,scale =1):
        text_vertices_list = []
        texcoords_list = []

        if self._hud.cursor.text: 
            text_len = (len(self._hud.cursor.text[0]),len(self._hud.cursor.text[1])) 
            rows = 1 + ceil(text_len[1] * self._hud._text_dim[0] / self._hud._cursor_text_box_max_width)
            text_box_width = text_len[0] * 5 * scale

            x_pos_offset  = 0
            for i in range(text_len[0]):
                char = self._hud.cursor.text[0][i]
                ord_val = ord(char)
                if 48 <= ord_val <= 57:
                    ind = ord_val - 48 
                    tex_coords = self._rm._text_texcoords["NUMBERS"][ind]
                    vertices = self._get_vertices_for_cursor_num(text_box_width,rows,0,i,scale)
                    x_pos_offset += 5 * scale
                elif 65 <= ord_val <= 90: 
                    ind = ord_val - 65 
                    tex_coords = self._rm._text_texcoords["CAPITAL"][ind]
                    vertices = self._get_vertices_for_cursor_text(text_box_width,rows,0,x_pos_offset,scale)
                    if ind == 12 or ind == 14:
                        x_pos_offset += 7 * scale
                    else: 
                        x_pos_offset += 5 * scale

                elif 97 <= ord_val <= 122:
                    ind = ord_val - 97
                    tex_coords = self._rm._text_texcoords["LOWER"][ind]
                    vertices = self._get_vertices_for_cursor_text(text_box_width,rows,0,x_pos_offset,scale)
                    if ind == 12 or ind == 14:
                        x_pos_offset += 7 * scale
                    else: 
                        x_pos_offset += 5 * scale
                else: 
                    x_pos_offset += 5 * scale

                text_vertices_list.append(vertices)
                texcoords_list.append(tex_coords)

            glViewport(0, 0, self._screen_res[0], self._screen_res[1])
            vertices_array = np.concatenate(text_vertices_list,axis=0)
            texture_coords_array= np.concatenate(texcoords_list,axis=0)
            
            buffer_data = np.column_stack((vertices_array,texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)

            
            vao = self.ctx.vertex_array(self._prog_draw, [
                (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
            ])

            # Use buffers and render
            self._rm.ui_item_atlas.use()
            self.ctx.screen.use()
            vao.render()

            # Free vertex data
            vbo.release()
            vao.release()
            self._hud.cursor.text = None




    def _get_vertices_for_cursor_text(self,text_box_width,rows,row_num,x_offset,scale):
        fbo_width,fbo_height = self.ctx.screen.size
        topleft = (self._hud.cursor.topleft[0]* self._true_to_native_ratio - text_box_width//2 ,\
                   self._hud.cursor.topleft[1]*self._true_to_native_ratio-(self._hud._text_dim[1]* scale+ 1))  
        
        width,height = self._hud._text_dim[0]*scale, self._hud._text_dim[1] * scale  

        x = 2. * (topleft[0]+x_offset) / fbo_width -1.
        y = 1. - 2. * (topleft[1]- 5*scale +row_num * self._hud._text_dim[1] * scale ) /fbo_height 
        w = 2. * width / fbo_width
        h = 2. * height / fbo_height
        vertices = np.array([(x,y),(x+w,y),(x,y-h),
                             (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)
        return vertices

    def _get_vertices_for_cursor_num(self,text_box_width,rows,row_num,i,scale):
        fbo_width,fbo_height = self.ctx.screen.size
        topleft = (self._hud.cursor.topleft[0]*self._true_to_native_ratio- text_box_width//2 ,\
                   self._hud.cursor.topleft[1]*self._true_to_native_ratio-(self._hud._text_dim[1]*scale + 1))   
        
        width,height = self._hud._text_dim[0]*scale, self._hud._text_dim[1]*scale  

        x = 2. * (topleft[0]+i*5*scale) / fbo_width -1.
        y = 1. - 2. * (topleft[1]-5*scale +row_num * self._hud._text_dim[1]*scale ) /fbo_height 
        w = 2. * width / fbo_width
        h = 2. * height / fbo_height
        vertices = np.array([(x,y),(x+w,y),(x,y-h),
                             (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)
        
        return vertices

        

       
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
        x = source.x / tex.width
        y = source.y / tex.height
        w = source.w / tex.width
        h = source.h / tex.height

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

    def _render_to_buf_lt(self,offset,interpolation_alpha):
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
            if dist(light.position,offset) > light.radius + self._diagonal:
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
                
                #light.cur_power = max(0,light.power * (light.life/light.maxlife))
                light.position = (int(light.illuminator.center[0]+light.illuminator.velocity[0]*interpolation_alpha) ,\
                                   int(light.illuminator.center[1]+light.illuminator.velocity[1]*interpolation_alpha))    
                
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

    def bind_hud(self,hud:"HUD") -> None: 
        self._hud = hud 

    def bind_player(self,player:"Player") -> None: 
        self._player = player 


    def bind_tilemap(self,tilemap:"Tilemap") -> None:
        self._tilemap = tilemap

    
    def bind_background(self,name:str) -> None: 
        resource_manager = ResourceManager.get_instance()
        self._background = resource_manager.get_background_of_name(name)
    
    
    def render_scene_with_lighting(self,offset,interpolation_alpha,screen_shake):
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
        self._fbo_ao.clear(0, 0, 0, 0)
        self._buf_lt.clear(0, 0, 0, 0)


        render_shake = (int((offset[0] -screen_shake[0])),int((offset[1] -screen_shake[1])))


        """
        
        position of 'hulls' or shadow objects, and the lights  are  offsetted.

        """


        # Send hull data to SSBOs
        self._send_hull_data(render_shake)

        # Render lights onto double buffer
        self._render_to_buf_lt(render_shake,interpolation_alpha)

        # Blur lightmap for soft shadows and render onto aomap
        self._render_aomap()

        # Render background masked with the lightmap
        self._render_background_layer(offset)

        # Render foreground onto screen
        self._render_foreground()


        # render text if any 
        self._render_text(scale = 2.8)

        
   
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


    def render_tile_panel(self,text_atl: moderngl.Texture,tile_panel:"TilePanel"):
        """
        Render the tile panel onto the foreground buffer.

        Meant to be used with the editor only. 
        
        """
        fbo = self._get_fbo(Layer_.FOREGROUND)
        categories_panel:"TileCategories" = tile_panel.categories
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

    """
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
       
    """

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

    def _render_particles(self,fbo,interpolation_alpha,camera_scroll):
        particle_system = self._ps 
        
        vertices_list = []
        texture_coords_list = []

        polygon_vertices = []
        polygon_indices = []


        for particle in list(particle_system._active_animation_particles):
            cur_frame = particle.animation.curr_frame()
            animationData = PARTICLE_ATLAS_POSITIONS_AND_SIZES[particle.type]
            if particle.rotation_angle != 0:
                pivot = PARTICLE_ANIMATION_PIVOTS[particle.type]
                vertices = self._create_rotated_vertices(animationData[1],(particle.pos[0]+particle.velocity[0]*interpolation_alpha-camera_scroll[0],\
                                                                           particle.pos[1]+particle.velocity[1]*interpolation_alpha-camera_scroll[1]),\
                                                                            particle.rotation_angle,pivot,particle.flipped)
            else: 
                vertices = self._create_animation_particle_vertices((particle.pos[0]+particle.velocity[0] *interpolation_alpha,particle.pos[1] +particle.velocity[1] * interpolation_alpha),\
                                                                    animationData[1],camera_scroll,fbo.width,fbo.height)
            
            texture_coords = particle_system._tex_dict[(particle.type,cur_frame)]
            vertices_list.append(vertices)
            texture_coords_list.append(texture_coords)

        if vertices_list: 
            vertices_array = np.concatenate(vertices_list,axis = 0)
            texture_coords_array = np.concatenate(texture_coords_list,axis = 0)

            buffer_data = np.column_stack((vertices_array,texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)

            self._render_animated_particles(vbo,fbo,self._rm.particles_atlas)
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
        #TODO: change the rendering logic so that it doesn't have to change the surface to a texture,
        # should be quite simple. 

        for particle in list(particle_system._active_collide_particles):
            buffer_surf = particle._buffer_surf
            tex = self.surface_to_texture(buffer_surf)
            self.render_texture(tex,Layer_.BACKGROUND,
                dest = pygame.Rect(particle._pos[0]+particle._velocity[0]*interpolation_alpha-camera_scroll[0],\
                                   particle._pos[1]+particle._velocity[1]*interpolation_alpha-camera_scroll[1],tex.width,tex.height),
                source = pygame.Rect(0,0,tex.width,tex.height)
            )
            tex.release()   

        # creating new fire particle system 
         
        """
        instance_data = []
        for particle in list(particle_system._active_fire_particles):
            instance_data.extend(self._create_fire_particle__instance_data(particle,interpolation_alpha,camera_scroll))

        instance_data = np.array(instance_data,dtype=np.float32)
        if instance_data.any():
            self._fire_instance_buffer.write(np.array(instance_data,dtype=np.float32).tobytes())
            self._vao_fire.render(moderngl.TRIANGLES,instances=len(self._ps._active_fire_particles))
        
        """        
        base_index = 0
        for spark in list(particle_system._active_sparks):
            vertices,indices = self._create_spark_vertices(spark,interpolation_alpha,camera_scroll,base_index)
            polygon_vertices.extend(vertices)
            polygon_indices.extend(indices)
            base_index +=4

        if polygon_vertices:
            vertex_data = np.array(polygon_vertices,dtype=np.float32)
            index_data = np.array(polygon_indices,dtype = 'i4')
            vbo = self.ctx.buffer(vertex_data.tobytes())
            ibo = self.ctx.buffer(index_data.tobytes())

            vao = self.ctx.vertex_array(self._prog_polygon_draw,[(vbo, '2f 3f', 'in_position','in_color')],ibo)

            vao.render(mode= moderngl.TRIANGLES)
            vao.release()
            vbo.release()
            ibo.release()

    def _create_fire_particle__instance_data(self,particle,interpolation_alpha,camera_scroll):
        scale_ratio = 2.4
        base_circle_pos = self._map_circle_coords_to_world_coords((particle.ren_x,particle.ren_y),interpolation_alpha,\
                                                                  particle.velocity,camera_scroll)

        if particle.i == 0:
            second_circle_pos = self._map_circle_coords_to_world_coords((particle.ren_x + randint(-1,1),particle.ren_y - 4),interpolation_alpha,\
                                                                        particle.velocity,camera_scroll)
            life_ratio = (particle.maxlife - particle.life) / particle.maxlife
            return [
                (*base_circle_pos,*normalize_color_arguments(*particle.palette[particle.i],particle.alpha),particle.r*scale_ratio /self._true_res[1] ),
                (*second_circle_pos,0,0,0,0,(particle.r *life_ratio/0.88)*scale_ratio/self._true_res[1])
            ]
        else: 
            second_circle_pos = self._map_circle_coords_to_world_coords((particle.ren_x+randint(-1,1),particle.ren_y -3),interpolation_alpha,\
                                                                        particle.velocity,camera_scroll)
            return [
                (*base_circle_pos,*normalize_color_arguments(*particle.palette[particle.i],particle.alpha),particle.r*scale_ratio/self._true_res[1]),
                (*second_circle_pos,*normalize_color_arguments(*particle.palette[particle.i-1],particle.alpha),(particle.r / 1.5)*scale_ratio/ self._true_res[1])
            ] 

    
    
    def _map_circle_coords_to_world_coords(self,pos,interpolation_alpha,velocity,camera_scroll):
        x = 2. * (pos[0]+velocity[0]*interpolation_alpha-camera_scroll[0]) / self._true_res[0] -1.
        y = 1. - 2 * (pos[1]+velocity[1]*interpolation_alpha-camera_scroll[1]) / self._true_res[1] 

        return (x,y)

    """
    pygame.draw.circle(bsurf, self.palette[self.i] + (self.alpha,), (self.ren_x - offset[0], self.ren_y - offset[1]), self.r, 0)
            
        if self.i == 0:
            life_ratio = (self.maxlife - self.life) / self.maxlife
            pygame.draw.circle(bsurf, (0, 0, 0, 0), (self.ren_x + random.randint(-1, 1) - offset[0], self.ren_y - 4 - offset[1]), self.r * (life_ratio / 0.88), 0)
        else:
            pygame.draw.circle(bsurf, self.palette[self.i - 1] + (self.alpha,), (self.ren_x + random.randint(-1, 1) - offset[0], self.ren_y - 3 - offset[1]), self.r / 1.5, 0)

    """


    def _create_spark_vertices(self,spark:"Spark",interpolation_alpha,camera_scroll,base_index):
        interpolation_offset = (spark.velocity[0] * interpolation_alpha,spark.velocity[1] * interpolation_alpha)
        vertices= [
                spark.pos[0]+interpolation_offset[0] -camera_scroll[0]+ cos(radians(spark.angle)) * spark.speed * spark.scale, spark.pos[1]+interpolation_offset[1]-camera_scroll[1] - sin(radians(spark.angle)) * spark.speed * spark.scale,
                spark.color[0],spark.color[1],spark.color[2],

                spark.pos[0]+interpolation_offset[0]-camera_scroll[0]+ cos(radians(spark.angle) + pi / 2) *spark.speed * spark.scale * 0.3, spark.pos[1]+interpolation_offset[1]-camera_scroll[1] - sin(radians(spark.angle) + pi / 2) * spark.speed * spark.scale * 0.3,
                spark.color[0],spark.color[1],spark.color[2],

                spark.pos[0]+interpolation_offset[0] -camera_scroll[0]- cos(radians(spark.angle)) * spark.speed * spark.scale * 3.5, spark.pos[1]+interpolation_offset[1] -camera_scroll[1]+ sin(radians(spark.angle)) * spark.speed * spark.scale * 3.5,
                spark.color[0],spark.color[1],spark.color[2],

                spark.pos[0]+interpolation_offset[0] -camera_scroll[0]+ cos(radians(spark.angle) - pi / 2) * spark.speed * spark.scale * 0.3, spark.pos[1]+interpolation_offset[1]-camera_scroll[1] + sin(radians(spark.angle) + pi / 2) * spark.speed * spark.scale * 0.3,
                spark.color[0],spark.color[1],spark.color[2],
        ]

        self._normalize_spark_vertex_data(vertices)
        indices = [
            base_index,base_index +1, base_index +2,
            base_index+2,base_index+3,base_index 
        ]
        return vertices,indices



    def _normalize_spark_vertex_data(self,coors):
        for i, coor in enumerate(coors):
            # normalize world coordinates to screen coors
            if i % 5 ==0:
                coors[i] = 2. * (coors[i]) / self._true_res[0] -1.
            elif i % 5 ==1: 
                coors[i] =  1. - 2. *(coors[i]) /self._true_res[1] 
            else: 
                # normalize color value
                coors[i] = coors[i] / 255

    
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


    def _render_grass(self,fbo:moderngl.Framebuffer,camera_scroll)->None: 
        if self._gm.ground_shadow[0]:
            shadow_offset = (camera_scroll[0] - self._gm.ground_shadow[3][0],camera_scroll[1] - self._gm.ground_shadow[3][1])
            for pos in self._gm.render_list: 
                self._render_grass_shadow(self._gm.grass_tiles[pos],shadow_offset)

        burning_grass_vertices_list = []
        burning_grass_texture_coords_list = []

        grass_vertices_list = []
        grass_texture_coords_list = []

        for key,tile in self._gm.burning_grass_tiles.items():
            if self._gm.base_pos[0] <= key[0]  <= self._gm.base_pos[0] + self._gm.visible_tile_range[0] and \
                self._gm.base_pos[1] <= key[1] <= self._gm.base_pos[1] + self._gm.visible_tile_range[1]:
                self._render_tile(fbo,key,tile,burning_grass_vertices_list,\
                                  burning_grass_texture_coords_list,camera_scroll)

        for pos in self._gm.render_list:
            tile = self._gm.grass_tiles[pos]
            self._render_tile(fbo,pos,tile,grass_vertices_list,
                              grass_texture_coords_list,camera_scroll)
        if grass_vertices_list: 
            vertices_array = np.concatenate(grass_vertices_list,axis = 0)
            texture_coords_array = np.concatenate(grass_texture_coords_list,axis=0 )

            buffer_data = np.column_stack((vertices_array,texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)
            vao = self.ctx.vertex_array(self._prog_draw,[(vbo, '2f 2f','vertexPos','vertexTexCoord')])
            
            self._rm._texture_atlasses[self._gm.ga.asset_name].use()
            fbo.use()
            vao.render()
            vbo.release()
            vao.release()
            
        



    def _render_grass_shadow(self,camera_scroll)->None: 
        pass 


    def _render_tile(self,fbo,base_pos,tile,vertices_list,
                     texture_coords_list,camera_scroll)->None: 
        if tile.custom_blade_data:
            blades = tile.custom_blade_data
        else: 
            blades = tile.blades 


        for blade in blades:
            # You have to render the shade, then the grass. 

            # grass parameters: 
            # blade[1] = blade id, blade[2] = variation, (blade[0][0] + tile.padding,blade[0][1] + tile.padding) = location 
            # rotation = max(-90, min(90,blade[3] + tile.true_rotation)), scale = tile.burn_life/tile.max_burn_life
            #vertices = self._create_blade_vertices(fbo,base_pos,tile.size,tile.padding,\
            #                                       blade,camera_scroll) 
            topleft=  (base_pos[0] * tile.size + blade[0][0] - camera_scroll[0],
                       base_pos[1] * tile.size + blade[0][1] -camera_scroll[1])
            rotation_angle = max(-90, min(90, blade[3] + tile.true_rotation))
            vertices = self._create_rotated_vertices(self._gm.ga.texture_dim,topleft,rotation_angle,
                                                     (self._gm.ga.texture_dim[0]//2,self._gm.ga.texture_dim[1]//2),False)
            texture_coords = self._rm._grass_asset_texture_coords[self._gm.ga.asset_name][blade[1]][blade[2]]

            vertices_list.append(vertices)
            texture_coords_list.append(texture_coords)
        """
        if vertices_list: 
            vertices_array = np.concatenate(vertices_list,axis = 0)
            texture_coords_array = np.concatenate(texture_coords_list,axis=0 )

            buffer_data = np.column_stack((vertices_array,texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)
            vao = self.ctx.vertex_array(self._prog_draw,[(vbo, '2f 2f','vertexPos','vertexTexCoord')])
            
            self._rm._texture_atlasses[self._gm.ga.asset_name].use()
            fbo.use()
            vao.render()
            vbo.release()
            vao.release()
        """
            
        

    def _create_blade_vertices(self,fbo,base_pos,tile_size,
                               padding,blade,offset) ->None: 

        topleft = (base_pos[0] * tile_size + blade[0][0],\
                       base_pos[1] * tile_size + blade[0][1]-padding)
        
        

        x = 2. * (topleft[0] - offset[0]) / self._true_res[0] - 1.
        y = 1. - 2. *(topleft[1] - offset[1]) / self._true_res[1] 
        w = 2. *(self._gm.ga.texture_dim[0]) / self._true_res[0] 
        h = 2. *(self._gm.ga.texture_dim[1]) / self._true_res[1]
        
        return np.array([(x,y),(x+w,y),(x,y-h),
                         (x,y-h), (x+w,y),(x+w,y-h)],dtype=np.float32)


    def _render_bullets(self,fbo:moderngl.Framebuffer,interpolation_alpha,camera_scroll):
        vertices_list= [] 
        texture_coords_list = []
        for bullet in self._em._bullets:
            interpolation_offset = (bullet.velocity[0] * interpolation_alpha, bullet.velocity[1] * interpolation_alpha) if bullet.interpolate_pos else (0,0)
            texture_coords = self._rm._bullet_texcoords[bullet.type]
            vertices = self._create_vertices_for_bullet(bullet.size,(bullet.center[0]+interpolation_offset[0] -camera_scroll[0],\
                                                                     bullet.center[1]+interpolation_offset[1] -camera_scroll[1]),bullet.angle,bullet.flip)
            
            vertices_list.append(vertices)
            texture_coords_list.append(texture_coords)

        if vertices_list:
            vertices_array = np.concatenate(vertices_list,axis=0)
            texture_coords_array =np.concatenate(texture_coords_list,axis=0) 

            buffer_data =np.column_stack((vertices_array,texture_coords_array)).astype(np.float32)
            vbo = self.ctx.buffer(buffer_data)
            vao = self.ctx.vertex_array(self._prog_draw,[(vbo,'2f 2f','vertexPos','vertexTexCoord')])

            fbo.use()
            self._rm.bullet_atlas.use()
            vao.render()
            vao.release()
            vbo.release()

            
    
    def _create_vertices_for_bullet(self,size,center,rotation_angle,flipped)->np.array:
        p0 = vec2(-size[0]//2, size[1]//2) # topleft 
        p1 = vec2(size[0]//2 , size[1]//2) # topright 
        p2 = vec2(-size[0]//2 , -size[1]//2) # bottomleft 
        p3 = vec2(size[0]//2 , -size[1]//2) # bottomright  

        # step 3: do the rotation.
        sign = 1 if rotation_angle> 0 else -1 
        if flipped:
            angle =  (180 - abs(rotation_angle)) * (-1) * sign
        else: 
            angle = rotation_angle
            
        p0.rotate_ip(angle)
        p1.rotate_ip(angle)
        p2.rotate_ip(angle)
        p3.rotate_ip(angle)

        p0 += center 
        p1 += center 
        p2 += center
        p3 += center
        # step 5: map the vertices to screen coords 

        self._map_world_coords_to_screen_coords(p0)        
        self._map_world_coords_to_screen_coords(p1)        
        self._map_world_coords_to_screen_coords(p2)        
        self._map_world_coords_to_screen_coords(p3)        

        # step 6: create the vertices array 
        if flipped: 
            tl = p1 
            tr = p0
            bl = p3
            br = p2 
        else: 
            tl = p0 
            tr = p1
            bl = p2
            br = p3
        return np.array([bl,br,tl,
                         tl,br,tr])


    def render_background_scene_to_fbo(self,offset = (0,0),interpolation_alpha:float = 0.0,infinite:bool = False)-> None :
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

        self._render_player(fbo,interpolation_alpha,offset)
        self._render_grass(fbo,offset)
        self._render_particles(fbo,interpolation_alpha,offset)
        self._render_bullets(fbo,interpolation_alpha,offset)

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
