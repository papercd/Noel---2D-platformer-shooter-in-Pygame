


def bresenham_line(x0, y0, x1, y1):
    """ Bresenham's Line Algorithm to get all points on a line, sampled at intervals """
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    max_points = max(dx, dy)
    step_size = max(1, max_points // 1)  # Adjust step_size as needed

    count = 0 
    while True:
        count +=1 
        if count > 100:
            break

        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = err * 2
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
        if len(points) % step_size == 0:
            points.append((x0, y0))

    return points

def tile_coordinates(x, y, tile_size):
    """ Convert pixel coordinates to tile coordinates """
    return int(x // tile_size) ,int( y // tile_size)


def line_of_sight(player_pos, entity_pos, tilemap, tile_size):
    """ Check if there is a line of sight between player and entity """

    start_x, start_y = player_pos[0] , player_pos[1]
    end_x, end_y = entity_pos[0], entity_pos[1]
    
    line_points = bresenham_line(start_x, start_y, end_x, end_y)
    
    for point in line_points:
        tile_x, tile_y = tile_coordinates(point[0], point[1], tile_size)
        tile_key = f"{tile_x};{tile_y}"

        if tile_key in tilemap:
            
            return False

    return True
