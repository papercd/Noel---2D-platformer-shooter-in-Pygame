from importlib import resources
from enum import Enum
import numpy as np
import moderngl
import pygame
import numbers
from OpenGL.GL import glBlitNamedFramebuffer, GL_COLOR_BUFFER_BIT, GL_NEAREST, glGetUniformBlockIndex, glUniformBlockBinding
import math
from scripts.background import Background
from my_pygame_light2d.shader import Shader 
from my_pygame_light2d.light import PointLight
from my_pygame_light2d.hull import Hull
from my_pygame_light2d.color import normalize_color_arguments, denormalize_color
from my_pygame_light2d.double_buff import DoubleBuff
from my_pygame_light2d.util import create_rotated_rect,to_dest_coords

BASE_PATH = 'data/images/'

class Layer_(Enum):
    BACKGROUND = 1,
    FOREGROUND = 2,


class LightingEngine:
    """A class for managing lighting effects within a Pygame environment."""

    def __init__(self,game, screen_res: tuple[int, int],screen_to_native_ratio : float, native_res: tuple[int, int], lightmap_res: tuple[int, int]) -> None:
        """
        Initialize the lighting engine.

        Args:
            native_res (tuple[int, int]): Native resolution of the game (width, height).
            lightmap_res (tuple[int, int]): Lightmap resolution (width, height).
        """

        # Initialize private members
        self._screen_to_native_ratio = screen_to_native_ratio
        self._screen_res = screen_res
        self._native_res = native_res
        self._diagonal = math.sqrt(self._native_res[0]**2 + self._native_res[1] **2)

        self._lightmap_res = lightmap_res
        self._ambient = (.25, .25, .25, .25)

        # Initialize public members
        self.lights: list[PointLight] = []
        self.hulls: list[Hull] = []
        self.shadow_blur_radius: int = 5
        self.game = game

        # Configure pygame
        self._check_and_configure_pygame()

        # Create an OpenGL context
        self.ctx = moderngl.create_context()

        # Load shaders
        self._load_shaders()

        # Create VAO and VBO
        self._create_screen_vertex_buffers()

        # Create render textures and corresponding FBOs
        self._create_frame_buffers()

        # Create SSBO for hull vertices
        self._create_ssbos()

    def _check_and_configure_pygame(self):
        # Check that pygame has been initialized
        assert pygame.get_init(), 'Error: Pygame is not initialized. Please ensure you call pygame.init() before using the lighting engine.'

        # Set OpenGL version to 3.3 core
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(
            pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        # Configure pygame display
        self._pygame_display = pygame.display.set_mode(
            self._screen_res, pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF)
        
        

        # initialize thorpy for gui elements 

    def _load_shaders(self):
        # Read source files
        #vertex_src = resources.read_text(
        #    'pygame_light2d', 'vertex.glsl')
        with open('my_pygame_light2d/vertex.glsl',encoding='utf-8') as file:
            vertex_src = file.read()

        with open('my_pygame_light2d/rotate_vertex.glsl',encoding='utf-8') as file:
            rotate_vertex_src = file.read()

        with open('my_pygame_light2d/fragment_rotate.glsl',encoding='utf-8') as file:
            fragment_src_rotate= file.read()


        fragment_src_light = resources.read_text(
            'pygame_light2d', 'fragment_light.glsl')
        fragment_src_blur = resources.read_text(
            'pygame_light2d', 'fragment_blur.glsl')

               
        # Read source files

        with open('my_pygame_light2d/fragment_mask.glsl', encoding='utf-8') as file:
           
            fragment_src_mask = file.read()
            
            try:
                self._prog_mask = self.ctx.program(vertex_shader=vertex_src, fragment_shader=fragment_src_mask)
            except Exception as e:
                print("Shader compilation or linking error:", e)
                return

            # Print all active uniforms to verify 'range' is present
            print("Active uniforms:")
            for uniform in self._prog_mask:
                print(uniform)
            
            try:
                print(self._prog_mask['range'])
            except KeyError:
                print("Uniform 'range' not found")

        with open('my_pygame_light2d/fragment_draw.glsl', encoding='utf-8') as file:
           
            fragment_src_draw = file.read()
            
            try:
                self._prog_draw = self.ctx.program(vertex_shader=vertex_src, fragment_shader=fragment_src_draw)
            except Exception as e:
                print("Shader compilation or linking error:", e)
                return

            # Print all active uniforms to verify 'range' is present
            print("Active uniforms:")
            for uniform in self._prog_draw:
                print(uniform)
            
            try:
                print(self._prog_draw['u_alpha'])
            except KeyError:
                print("Uniform 'u_alpha' not found")

        # Create shader programs
        

        self._prog_light = self.ctx.program(vertex_shader=vertex_src,
                                            fragment_shader=fragment_src_light)
        self._prog_blur = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader=fragment_src_blur)
        
        self._prog_draw = self.ctx.program(vertex_shader=vertex_src,
                                           fragment_shader=fragment_src_draw)
        
        self._prog_rotate = self.ctx.program(vertex_shader= rotate_vertex_src,
                                             fragment_shader=fragment_src_rotate)


    def set_alpha_value_draw_shader(self,alpha_value : float) -> None:
        """
        set the alpha value uniform for the draw shader.        
        
        """
        assert  0<= alpha_value <=1

        self._prog_draw['u_alpha'].value = alpha_value


        


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

   

    def release_objects(self):
        self._prog_rotate.release()
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


    def _release_frame_buffers(self):
        self._tex_bg.release()
        #self._tex_bg.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fbo_bg.release()

        self._tex_fg.release()
        #self._tex_fg.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fbo_fg.release()

        # Double buffer for lights
        self._buf_lt.release()

        # Ambient occlussion map
        self._tex_ao.release()
        
        self._fbo_ao.release()

        

    def _create_frame_buffers(self):
        # Frame buffers
        self._tex_bg = self.ctx.texture(self._native_res, components=4)
        self._tex_bg.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self._fbo_bg = self.ctx.framebuffer([self._tex_bg])

        self._tex_fg = self.ctx.texture(self._native_res, components=4)
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
        return self._native_res 


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

    def render_texture(self, tex: moderngl.Texture, Layer_: Layer_, dest: pygame.Rect, source: pygame.Rect,angle:float=0.0,flip : tuple[bool,bool]= (False,False)):
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
        fbo = self._get_fbo(Layer_)
        self._test_render_tex_to_fbo(tex, fbo, dest, source , angle,flip)

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

    def render_background_view(self,background:Background,offset = (0,0)):
        
        scroll = offset[0]
        speed = 1
        
    
        for texture in background.bg_layers:
            for panels in range(-1, 2):
                self.render_texture_with_trans(
                    texture, Layer_.BACKGROUND,
                    position= (panels*texture.width -scroll *0.05*speed,\
                               0 - min(0, offset[1] * 0.05)),                
                
                )
            speed += 1


    def render_tilemap(self,tilemap,offset:tuple[int,int],in_editor : bool = False) -> None:
        if in_editor:
            texture_source = self.game.assets
        else: 
            texture_source = self.game.general_sprites
        
        for x_cor in range(offset[0] // tilemap.tile_size, (offset[0] + self._native_res[0]) // tilemap.tile_size+1):
            for y_cor in range(offset[1] // tilemap.tile_size, (offset[1] + self._native_res[1]) // tilemap.tile_size+1): 
                coor = str(x_cor) + ';' + str(y_cor)
                for dict in tilemap.offgrid_tiles:
                    
                    if coor in dict: 
                        tile = dict[coor]
                        variant_sub = tile.variant.split(';')

                        if tile.type.endswith('door') and tile.type.split('_')[0] != 'trap':
                            tex = texture_source[tile.type + '_' + variant_sub[0]][int(variant_sub[0])]
                            self.render_texture(
                                tex,Layer_.BACKGROUND,
                                dest=pygame.Rect(tile.pos[0] * tilemap.tile_size - offset[0] , tile.pos[1] * tilemap.tile_size - offset[1],tex.width,tex.height),
                                source=pygame.Rect(0,0,tex.width,tex.height)
                            )
                            
                            #surf.blit(sprite_source[tile.type + '_' + variant_sub[0]][int(variant_sub[0])],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1])) 

                        else: 
                            if isinstance(texture_source[tile.type][int(variant_sub[0])],list):
                            #if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):
                                tex = texture_source[tile.type][int(variant_sub[0])][int(variant_sub[1])]

                                self.render_texture(
                                    tex,Layer_.BACKGROUND,
                                    dest=pygame.Rect(tile.pos[0] * tilemap.tile_size - offset[0] , tile.pos[1] * tilemap.tile_size - offset[1],tex.width,tex.height),
                                    source=pygame.Rect(0,0,tex.width,tex.height)
                                )

                        
                                #surf.blit(texture_source[tile.type][int(variant_sub[0])][int(variant_sub[1])],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                            else: 
                                tex = texture_source[tile.type][int(variant_sub[0])]
                                self.render_texture(
                                    tex,Layer_.BACKGROUND,
                                    dest=pygame.Rect(tile.pos[0] * tilemap.tile_size - offset[0] , tile.pos[1] * tilemap.tile_size - offset[1],tex.width,tex.height),
                                    source=pygame.Rect(0,0,tex.width,tex.height)
                                )
                               
                                #surf.blit(texture_source[tile.type][int(variant_sub[0])],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
    

                                                
                        #you also gotta blit an alpha surface depending on their exposure ( how many neighbors they have. )
                        #render the mask 
                        #surf.blit(self.game.assets['masks'][int(variant_sub[0])], (tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
            
        #tiles rendering, render the decals here as well. 

        for x_cor in range(offset[0] // tilemap.tile_size, (offset[0] + self._native_res[0]) // tilemap.tile_size+1):
            for y_cor in range(offset[1] // tilemap.tile_size, (offset[1] + self._native_res[1]) //tilemap.tile_size +1): 
                coor = str(x_cor) + ';' + str(y_cor)
                if coor in tilemap.tilemap: 
                    tile = tilemap.tilemap[coor]
                    variant_sub = tile.variant.split(';')

                    if tile.type.endswith('door'):
                        # Blit the animation frame. 
                        if tile.open:
                            tile.cur_frame = min(tile.animation.count-1, tile.cur_frame+1)
                            tex = tile.animation.textures[tile.cur_frame]

                            self.render_texture(
                                tex,Layer_.BACKGROUND,
                                dest=pygame.Rect(tile.pos[0] * tilemap.tile_size - offset[0] , tile.pos[1] * tilemap.tile_size - offset[1],tex.width,tex.height),
                                source=pygame.Rect(0,0,tex.width,tex.height)
                            )
                           

                            
                            #surf.blit(tile.animation.images[tile.cur_frame],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]) )
                        else: 
                            tile.cur_frame = max(0, tile.cur_frame -1)
                            tex = tile.animation.textures[tile.cur_frame]
                            self.render_texture(
                                tex,Layer_.BACKGROUND,
                                dest=pygame.Rect(tile.pos[0] * tilemap.tile_size - offset[0] , tile.pos[1] * tilemap.tile_size - offset[1],tex.width,tex.height),
                                source=pygame.Rect(0,0,tex.width,tex.height)
                            )
                            
                            
                            #surf.blit(tile.animation.images[tile.cur_frame],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1])) 
                        
                        #surf.blit(self.game.interactables[tile.type + '_' +variant_sub[0]].images[tile.cur_frame],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))  

                    else: 
                        if isinstance(texture_source[tile.type][int(variant_sub[0])],list):
                        #if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):
                            tex = texture_source[tile.type][int(variant_sub[0])][int(variant_sub[1])]
                            self.render_texture(
                                tex,Layer_.BACKGROUND,
                                dest=pygame.Rect(tile.pos[0] * tilemap.tile_size - offset[0] , tile.pos[1] * tilemap.tile_size - offset[1],tex.width,tex.height),
                                source=pygame.Rect(0,0,tex.width,tex.height)
                            )
                            

                            #surf.blit(texture_source[tile.type][int(variant_sub[0])][int(variant_sub[1])],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                        else:
                            tex =  texture_source[tile.type][int(variant_sub[0])]
                            self.render_texture(
                                tex,Layer_.BACKGROUND,
                                dest=pygame.Rect(tile.pos[0] * tilemap.tile_size - offset[0] , tile.pos[1] * tilemap.tile_size - offset[1],tex.width,tex.height),
                                source=pygame.Rect(0,0,tex.width,tex.height)
                            )

                            #surf.blit(texture_source[tile.type][int(variant_sub[0])],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))

                        if in_editor and tile.type in tilemap.PHYSICS_APPLIED_TILE_TYPES and tile.dirty:
                            temp_surf = pygame.Surface((tilemap.tile_size,tilemap.tile_size),pygame.SRCALPHA)
                            pygame.draw.rect(temp_surf,(255,12,12),(0,0,tilemap.tile_size,tilemap.tile_size),width= 1)
                            red_square_tex = self.surface_to_texture(temp_surf) 
                            self.render_texture(
                                red_square_tex,Layer_.BACKGROUND,
                                dest=pygame.Rect(tile.pos[0] * tilemap.tile_size - offset[0] , tile.pos[1] * tilemap.tile_size - offset[1],red_square_tex.width,red_square_tex.height),
                                source=pygame.Rect(0,0,red_square_tex.width,red_square_tex.height)
                            )
                            red_square_tex.release()
                            #pygame.draw.rect(surf,(255,12,12), (tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1],self.tile_size,self.tile_size),width = 1)

                        #you also gotta blit an alpha surface depending on their exposure ( how many neighbors they have. )
                        #render the mask 
                        #surf.blit(self.game.assets['masks'][int(variant_sub[0])], (tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                        for decal in tile.decals.copy():
                            #so decals need to be surface objects. 
                            pass
                            """
                            surf.blit(decal[0],(tile.pos[0] * self.tile_size-offset[0], tile.pos[1] *self.tile_size-offset[1]))
                            decal[1] += 1
                            if decal[1] >= 40:
                                tile.decals.remove(decal)
                            """

        #decorations rendering 
        
        for tile in tilemap.decorations: 
            
                variant_sub = tile.variant.split(';')
                if isinstance(texture_source[tile.type][int(variant_sub[0])],list):
                #if isinstance(self.game.assets[tile.type][int(variant_sub[0])],list):
                    tex = texture_source[tile.type][int(variant_sub[0])][int(variant_sub[1])]
                    self.render_texture(
                                tex,Layer_.BACKGROUND,
                                dest=pygame.Rect(tile.pos[0] - offset[0] , tile.pos[1] - offset[1],tex.width,tex.height),
                                source=pygame.Rect(0,0,tex.width,tex.height)
                            )
                   
                    #surf.blit(texture_source[tile.type][int(variant_sub[0])][int(variant_sub[1])], (tile.pos[0] - offset[0],tile.pos[1]-offset[1]))
                else: 
                    tex =  texture_source[tile.type][int(variant_sub[0])]
                    self.render_texture(
                                tex,Layer_.BACKGROUND,
                                dest=pygame.Rect(tile.pos[0] - offset[0] , tile.pos[1] - offset[1],tex.width,tex.height),
                                source=pygame.Rect(0,0,tex.width,tex.height)
                            )
                    
                    

                    #surf.blit(texture_source[tile.type][int(variant_sub[0])], (tile.pos[0] - offset[0],tile.pos[1]-offset[1]))
        


    def render_items(self,items,offset = (0,0)):
        pass 
        
    


    def render(self,range,offset,screen_shake):
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
        self._render_to_buf_lt(range,render_shake)

        # Blur lightmap for soft shadows and render onto aomap
        self._render_aomap()

        # Render background masked with the lightmap
        self._render_background(range,offset)

        # Render foreground onto screen
        self._render_foreground()

    def _point_to_uv(self, p: tuple[float, float]):
        return [p[0]/self._native_res[0], 1 - (p[1]/self._native_res[1])]

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

    def _render_tex_to_fbo(self, tex: moderngl.Texture, fbo: moderngl.Framebuffer, dest: pygame.Rect, source: pygame.Rect):
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


    def _second_test_render_tex_to_fbo(self, tex: moderngl.Texture, fbo: moderngl.Framebuffer, dest: pygame.Rect, source: pygame.Rect,
                            rotation: float = 0.0, flip: tuple[bool, bool] = (False, False)):
        # Center of rotation (pivot point) in texture space
        pivot_x = dest.w / 2
        pivot_y = dest.h / 2

        # Compute the vertices around the pivot
        angle_cos = np.cos(rotation)
        angle_sin = np.sin(rotation)
        
        # Offset vertices by -pivot, rotate, and translate back
        rotated_vertices = [
            ((-pivot_x) * angle_cos - (-pivot_y) * angle_sin + pivot_x, (-pivot_x) * angle_sin + (-pivot_y) * angle_cos + pivot_y),
            ((pivot_x) * angle_cos - (-pivot_y) * angle_sin + pivot_x, (pivot_x) * angle_sin + (-pivot_y) * angle_cos + pivot_y),
            ((-pivot_x) * angle_cos - (pivot_y) * angle_sin + pivot_x, (-pivot_x) * angle_sin + (pivot_y) * angle_cos + pivot_y),
            ((pivot_x) * angle_cos - (pivot_y) * angle_sin + pivot_x, (pivot_x) * angle_sin + (pivot_y) * angle_cos + pivot_y),
        ]

        # Find bounding box for rotated vertices
        x_coords, y_coords = zip(*rotated_vertices)
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        # Compute width and height of the new bounding box
        new_width = max_x - min_x
        new_height = max_y - min_y

        # Translate dest rect so that its top-left corner aligns with the rotated bounding box's top-left corner
        dest_x = dest.x - min_x
        dest_y = dest.y - min_y

        # Map destination rect to screen space coordinates
        width, height = fbo.size
        x = 2. * dest_x / width - 1.
        y = 1. - 2. * dest_y / height
        w = 2. * new_width / width
        h = 2. * new_height / height

        vertices = np.array([
            (x, y), (x + w, y), (x, y - h),
            (x, y - h), (x + w, y), (x + w, y - h)
        ], dtype=np.float32)

        # Texture coordinates (apply flipping)
        tx = source.x / tex.size[0]
        ty = source.y / tex.size[1]
        tw = source.w / tex.size[0]
        th = source.h / tex.size[1]

        tex_coords = np.array([
            (tx, ty + th), (tx + tw, ty + th), (tx, ty),
            (tx, ty), (tx + tw, ty + th), (tx + tw, ty)
        ], dtype=np.float32)

        """"
        # Apply flip if specified
        if flip[0]:  # Horizontal flip
            tex_coords[:, 0] = 1.0 - tex_coords[:, 0]
        if flip[1]:  # Vertical flip
            tex_coords[:, 1] = 1.0 - tex_coords[:, 1]
        """

        # Create buffers and load into VAO
        buffer_data = np.hstack([vertices, tex_coords])
        vbo = self.ctx.buffer(buffer_data)
        vao = self.ctx.vertex_array(self._prog_draw, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Set rotation and flip uniforms
        self._prog_draw['rotation'].value = rotation
        self._prog_draw['flip_horizontal'].value = flip[0]
        self._prog_draw['flip_vertical'].value = flip[1]

        # Use buffers and render
        tex.use()
        fbo.use()
        vao.render()

        # Free vertex data
        vbo.release()
        vao.release()

        # Reset uniforms
        self._prog_draw['rotation'].value = 0
        self._prog_draw['flip_horizontal'].value = False
        self._prog_draw['flip_vertical'].value = False


    def create_rotated_texture(self, source_texture: moderngl.Texture, 
                            rotation_angle: float, pivot: tuple[float, float]) -> moderngl.Texture:
        """
        Creates a rotated texture from a given texture and returns the new rotated texture
        contained within a fitting bounding box.
        
        Args:
            source_texture (moderngl.Texture): The source texture to rotate.
            rotation_angle (float): Rotation angle in radians.
            pivot (tuple[float, float]): The pivot point for the rotation, given as (x, y) coordinates.
            
        Returns:
            moderngl.Texture: A new texture containing the rotated image within a fitting bounding box.
        """
        src_width, src_height = source_texture.size

        # Calculate the bounding box size after rotation
        cos_angle = abs(np.cos(rotation_angle))
        sin_angle = abs(np.sin(rotation_angle))
        new_width = int(src_width * cos_angle + src_height * sin_angle)
        new_height = int(src_width * sin_angle + src_height * cos_angle)

        # Create a framebuffer and a new texture for the rotated output
        rotated_texture = self.ctx.texture((new_width, new_height), 4)
        rotated_texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        fbo = self.ctx.framebuffer(rotated_texture)

        # Compute the translation to center the pivot in the new bounding box
        pivot_offset_x = pivot[0] - src_width / 2.0
        pivot_offset_y = pivot[1] - src_height / 2.0
        translation_x = new_width / 2.0 - pivot_offset_x
        translation_y = new_height / 2.0 - pivot_offset_y

        # Prepare the vertices and texture coordinates
        vertices = np.array([
            (-src_width / 2, src_height / 2), (src_width / 2, src_height / 2), (-src_width / 2, -src_height / 2),
            (-src_width / 2, -src_height / 2), (src_width / 2, src_height / 2), (src_width / 2, -src_height / 2),
        ], dtype=np.float32)

        tex_coords = np.array([
            (0.0, 1.0), (1.0, 1.0), (0.0, 0.0),
            (0.0, 0.0), (1.0, 1.0), (1.0, 0.0),
        ], dtype=np.float32)

        # Create buffer data and set up vertex array object
        buffer_data = np.hstack([vertices, tex_coords])
        vbo = self.ctx.buffer(buffer_data)
        vao = self.ctx.vertex_array(self._prog_rotate,[
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Set rotation matrix for pivot rotation
        rotation_matrix = np.array([
            [cos_angle, -np.sin(rotation_angle), 0.0],
            [np.sin(rotation_angle), cos_angle, 0.0],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

        # Set uniforms for rotation, translation, and texture
        vao.program['rotation_matrix'].write(rotation_matrix.tobytes())
        vao.program['translation'].value = (translation_x / new_width * 2.0 - 1.0, 1.0 - translation_y / new_height * 2.0)
        vao.program['source_texture'].value = 0

        # Render the rotated texture to the new framebuffer
        source_texture.use(0)
        fbo.use()
        fbo.clear(0.0, 0.0, 0.0, 0.0)
        vao.render()

        # Clean up resources
        vbo.release()
        vao.release()
        fbo.release()

        return rotated_texture


    def _test_render_tex_to_fbo(self, tex: moderngl.Texture, fbo: moderngl.Framebuffer, dest: pygame.Rect, source: pygame.Rect,
                       rotation: float = 0.0, flip: tuple[bool,bool] = (False,False)):
        # Mesh for destination rect on screen
        width, height = fbo.size
        x = 2. * dest.x / width - 1.
        y = 1. - 2. * dest.y / height
        w = 2. * dest.w / width
        h = 2. * dest.h / height

        vertices = np.array([
            (x, y), (x + w, y), (x, y - h),
            (x, y - h), (x + w, y), (x + w, y - h)
        ], dtype=np.float32)

        # Texture coordinates (top-left to bottom-right)
        tx = source.x / tex.size[0]
        ty = source.y / tex.size[1]
        tw = source.w / tex.size[0]
        th = source.h / tex.size[1]

        tex_coords = np.array([
            (tx, ty + th), (tx + tw, ty + th), (tx, ty),
            (tx, ty), (tx + tw, ty + th), (tx + tw, ty)
        ], dtype=np.float32)

        buffer_data = np.hstack([vertices, tex_coords])
        vbo = self.ctx.buffer(buffer_data)
        vao = self.ctx.vertex_array(self._prog_draw, [
            (vbo, '2f 2f', 'vertexPos', 'vertexTexCoord'),
        ])

        # Set rotation and flip uniforms
        self._prog_draw['rotation'].value = rotation
        self._prog_draw['flip_horizontal'].value = flip[0]
        self._prog_draw['flip_vertical'].value = flip[1]

        # Use buffers and render
        tex.use()
        fbo.use()
        vao.render()

        # Free vertex data
        vbo.release()
        vao.release()

        self._prog_draw['rotation'].value = 0
        self._prog_draw['flip_horizontal'].value = False
        self._prog_draw['flip_vertical'].value = False 



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

    def _render_to_buf_lt(self,range,offset):
        # Disable alpha blending to render lights
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
            self._prog_light['native_width'] = self._native_res[0]
            self._prog_light['native_height'] = self._native_res[1]

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


    def _render_background(self,range,offset):
        self.ctx.screen.use()
        self._tex_bg.use()

        self._tex_ao.use(1)

        # calculate lowerBound and upper bound values to pass to shader 
      
       
        self._prog_mask['lightmap'].value = 1
        self._prog_mask['ambient'].value = self._ambient

        #self._prog_mask['range'].value = ((range[0] - offset[0])/self._native_res[0],(range[1] - offset[0])/self._native_res[0])
        
        self._vao_mask.render()

    def _render_foreground(self):
        self.ctx.screen.use()
        self._tex_fg.use()
        self._vao_draw.render()


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

    def calculate_render_position_with_offset(self,pos,offset = (0,0) )->tuple[float,float]:
        """
        helper function to calculate what the render position of a entity 
        texture would be with render scroll taken into consideration.

        meant to be used when using the render_texture_with_trans function. 
        
        """
        return ((pos[0] - offset[0])/self._screen_to_native_ratio,(pos[1] - offset[1])/self._screen_to_native_ratio)


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