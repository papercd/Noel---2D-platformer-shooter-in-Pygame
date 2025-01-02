import numpy as np 


screen_vertices = np.array([(-1.0, 1.0), (1.0, 1.0), (-1.0, -1.0),
                                    (-1.0, -1.0), (1.0, 1.0), (1.0, -1.0)], dtype=np.float32)
screen_tex_coords = np.array([(0.0, 1.0), (1.0, 1.0), (0.0, 0.0),
                                (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)], dtype=np.float32)
screen_vertex_data = np.hstack([screen_vertices, screen_tex_coords])


print(screen_vertex_data)