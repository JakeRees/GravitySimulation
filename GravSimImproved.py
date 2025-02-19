import ctypes
import math
import os
import random
import time

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame  # import after disabling environ prompt
import tkinter as tk

root = tk.Tk()  # create only one instance for Tk()
root.withdraw()  # keep the root window from appearing
pygame.font.init()

# Defining a few constants
damping_force = 1.1
pi = 3.1415926
G = 0
objects = []
to_remove = []
planet_colours = [(255, 255, 255), (255, 255, 220), (255, 245, 200), (255, 230, 190), (255, 210, 160), (255, 190, 140), (255, 160, 120), (255, 130, 110),  (255, 100, 90), (255, 75, 75)]
trail_colours = [(125, 125, 125), (125, 125, 110), (125, 122, 100), (125, 115, 95), (125, 105, 80), (125, 95, 70), (125, 80, 60), (125, 65, 55),  (125, 50, 45), (125, 35, 35)]

ctypes.windll.user32.SetProcessDPIAware()
win_width = round(ctypes.windll.user32.GetSystemMetrics(0) * 0.9)
win_height = round(ctypes.windll.user32.GetSystemMetrics(1) * 0.9)

print(str(win_width) + " | " + str(win_height))

mainFont = pygame.font.SysFont('Comic Sans MS', 15)
main_title_font = pygame.font.SysFont('impact', int(win_width*0.04))
sub_title_font = pygame.font.SysFont('impact', int(win_width*0.03))
embedded_title_font = pygame.font.SysFont('arial', int(win_width*0.025), True)
main_button_font = pygame.font.SysFont('arial', int(win_width*0.02), True)
general_text = pygame.font.SysFont('arial', int(win_width*0.02))
settings_text = pygame.font.SysFont('arial', int(win_width*0.015))
small_text = pygame.font.SysFont('arial', int(win_width*0.012))
tiny_text = pygame.font.SysFont('arial', int(win_width*0.01))

# Create surfaces
trails = pygame.surface.Surface((win_width, win_height))
screen = pygame.surface.Surface((win_width, win_height))
main_menu = pygame.surface.Surface((win_width, win_height))


# Defined by centre, half width, half height, index
"""
quadrants = []
force_calc_num = 0

ind = 0
for i in range (0, 2):
    for j in range (0, 2):
        ind += 1
        width = win_width / 4
        height = win_height / 4
        centre = [width + 2 * width * i, height + 2 * height * j]
        quadrants.append([width, height, centre, ind])

print(quadrants)
"""

# Declaring class for any object with mass
class Object:
    def __init__(self, x, y, mass, radius, velocity, can_move):
        self.x = x
        self.y = y
        self.mass = mass
        self.radius = radius
        self.can_move = can_move
        colours = calculate_colour(radius)
        self.colour, self.trail_colour = colours[0], colours[1]
        self.velocity = velocity
        self.frc = [0, 0]
        self.force_calculated = False
    def draw(self, screen, trail_screen, show_trails, min_trail_radius):
        pygame.draw.circle(screen, self.colour, (self.x, self.y), self.radius)
        if show_trails:
            if self.radius >= min_trail_radius:
                pygame.draw.circle(trail_screen, self.trail_colour, (self.x, self.y), 1)


def calculate_colour(radius):
    if int(radius) > 10:
        colour_index = 9
    else:
        colour_index = int(radius) - 1

    return planet_colours[colour_index], trail_colours[colour_index]


def blit_text(surface, text, position):
    surface.blit(text, position)


# Simple function to calculate the magnitude of a vector
def get_magnitude(vector):
    return math.sqrt(vector[0]**2 + vector[1]**2)


# Simple function to calculate the radius of an object based on it's mass
def calculate_radius(mass):
    return math.pow(mass*(10/3), 1/3)

"""
def check_zones(position, radius):
    zones_in = []
    
    for zone in quadrants:
        delta_x = position[0] - max(zone[2][0] - zone[0], min(position[0], zone[2][0] + zone[0]))
        delta_y = position[1] - max(zone[2][1] - zone[1], min(position[1], zone[2][1] + zone[1]))
        if (delta_x**2 + delta_y**2) < (radius**2):
            zones_in.append(zone[3])
    return zones_in
"""

def calculate_orbital_velocity(obj, immovable):

    dir_vector = [obj.x - immovable.x, obj.y - immovable.y]
    r = get_magnitude(dir_vector)
    speed = math.sqrt((G*(immovable.mass + obj.mass))/r)
    tangent_vector = [-dir_vector[1], dir_vector[0]]
    normalised_tangent_vector = [tangent_vector[0] / r, tangent_vector[1] / r]
    return normalised_tangent_vector[0]*speed, normalised_tangent_vector[1]*speed


def get_start_position_vector(distance, position):

    ranAngle = random.randrange(-180, 180)
    if ranAngle >= 0 and ranAngle < 90:
        x_distance = distance * math.cos(math.radians(ranAngle))
        y_distance = distance * math.sin(math.radians(ranAngle))
    elif ranAngle == 90:
        x_distance = 0
        y_distance = distance
    elif ranAngle > 90:
        x_distance = -distance * math.cos(math.radians(180 - ranAngle))
        y_distance = distance * math.sin(math.radians(180 - ranAngle))
    elif ranAngle >= -180 and ranAngle < -90:
        x_distance = distance * math.cos(math.radians(ranAngle))
        y_distance = distance * math.sin(math.radians(ranAngle))
    elif ranAngle == -90:
        x_distance = 0
        y_distance = -distance
    else:
        x_distance = distance * math.cos(math.radians(ranAngle))
        y_distance = distance * math.sin(math.radians(ranAngle))

    return [position[0] + x_distance, position[1] + y_distance]


#Function which returns the gravitational force vector between two objects
def calculate_gravitational_force(m, M, r, direction_vector):

    if r != 0:
        force_magnitude = -G*((M*m)/(r**2))
        normalised_direction_vector = [direction_vector[0] / r, direction_vector[1] / r]
        force_vector = [force_magnitude*normalised_direction_vector[0], force_magnitude*normalised_direction_vector[1]]
        return force_vector


# Calculates the total force vector acting on an object
def calculate_total_force_vector(target):
    global force_calc_num
    for obj in objects:
        if obj != target and not obj.force_calculated:
            dir_vector = [obj.x - target.x, obj.y - target.y]
            magnitude = get_magnitude(dir_vector)

            if magnitude < (40 + 2.2 * obj.mass) or not target.can_move:
                force_calc_num += 1
                partial_force_vector = calculate_gravitational_force(target.mass, obj.mass, magnitude, dir_vector)
                if partial_force_vector:
                    target.frc = [target.frc[0] - partial_force_vector[0], target.frc[1] - partial_force_vector[1]]
                    obj.frc = [obj.frc[0] + partial_force_vector[0], obj.frc[1] + partial_force_vector[1]]

    target.force_calculated = True


def calculate_collisions_velocity(mass1, mass2, velocity1, velocity2):
    total_mass = mass1 + mass2

    v_x = (mass1 * velocity1[0] + (mass2 * velocity2[0])) / total_mass
    v_y = (mass1 * velocity1[1] + (mass2 * velocity2[1])) / total_mass

    v_final = [
        v_x,
        v_y,
    ]

    return v_final


def detect_collisions(target):

    for obj in objects:
        if obj != target:
                    if target.mass > obj.mass:
                        larger = target
                        smaller = obj
                    else:
                        larger = obj
                        smaller = target

                    distance = get_magnitude([obj.x - target.x, obj.y - target.y])

                    if distance <= larger.radius + round(smaller.radius/2):
                        #new_velocity = calculate_collisions_velocity(larger.mass, smaller.mass, target.velocity, obj.velocity)
                        larger.mass += smaller.mass
                        #larger.velocity = new_velocity
                        larger.radius = calculate_radius(larger.mass)
                        larger.colour, larger.trail_colour = calculate_colour(larger.radius)
                        to_remove.append(smaller)


def create_objects(amount, centre_mass, min_mass, max_mass, random_mass, asteroid_num, asteroid_dist, asteroid_belt_num, number_density):

    number_densities = [0.18, 0.34, 0.48, 0.6, 0.7, 0.79, 0.87, 0.93, 0.97, 1]
    radial_zone_length = win_height / round(100/number_density)

    zone_num = 1

    for i in range(amount + 1):
        if i == 0:

            objects.append(Object(win_width / 2, win_height / 2, centre_mass, calculate_radius(centre_mass), [0, 0], False))

        else:

            if i <= (amount*number_densities[zone_num-1]):

                    radius_extra = objects[0].radius + radial_zone_length * (zone_num)
                    ran_distance = random.randrange(int(radius_extra), int(radius_extra + radial_zone_length))
            else:
                radius_extra = objects[0].radius + radial_zone_length * (zone_num)
                ran_distance = random.randrange(int(radius_extra), int(radius_extra + radial_zone_length))
                zone_num += 1

            position = get_start_position_vector(ran_distance, [win_width/2, win_height/2])

            if random_mass == 1:
                mass = random.randrange(min_mass, max_mass+1)
            else:
                mass = min_mass

            radius = calculate_radius(mass)
            temp_obj = Object(position[0], position[1], mass, radius, [0, 0], True)
            objects.append(temp_obj)
            temp_obj.velocity = calculate_orbital_velocity(temp_obj, objects[0])

    if asteroid_belt_num != 0:
        for i in range(asteroid_belt_num):
            for j in range(asteroid_num[i]):
                extra_radius = int(objects[0].radius + asteroid_dist[i])
                ran_distance = random.randrange(extra_radius, extra_radius + 15)
                position = get_start_position_vector(ran_distance, [win_width/2, win_height/2])
                temp_obj = Object(position[0], position[1], 1, 1, [0, 0], True)
                objects.append(temp_obj)
                temp_obj.velocity = calculate_orbital_velocity(temp_obj, objects[0])


def startup():
    global G
    setup = input("Would you like the default setup (type 0) the simple setup (type 1) or the advanced setup (type 2)")
    G = 0.0001
    start_num, centre_mass, min_mass, max_mass, random_mass, asteroids, asteroid_num, asteroid_dist, asteroid_belt_num, video_frame_rate, number_density = 0, 250, 1, 1, 1, 1, [], [], 0, 15, 5

    start_num = input("How many objects would you like to simulate? ")


    if setup != "0":
        G = float(input("Please input a value for G (0.0001 is the default) "))
        centre_mass = input("Please input a value for the stars mass (250 is the default) ")
        random_mass = int(input("Would you like to give the objects a constant mass? (0) or a random mass (1)? "))

        if random_mass == 1:
            min_mass = input("What minimum mass and size should your objects be? ")
            max_mass = input("What maximum mass and size should your objects be? ")
        else:
            mass = input("What mass and size should your objects be? ")
            min_mass = mass
        number_density = input("How densely packed would you like the objects to be (Default is 5, the higher the number to *less* dense) ")

        if setup == "1":

            asteroid_belt_num = int(input("How many astroid belts would you like to add "))

            for i in range(1, asteroid_belt_num + 1):
                asteroid_num.append(50 * i)
                asteroid_dist.append((win_height/10) * i)
        else:

            asteroid_belt_num = int(input("How many astroid belts would you like to add "))

            for i in range(0, asteroid_belt_num):
                asteroid_num.append(int(input("How many asteroids would you like in belt " + str(i+1) + "? ")))
                asteroid_dist.append((win_height/10) * int(input("How far away from the star should belt " + str(i+1) + " be? (Default is 1)? ")))

    video_frame_rate = input("After how many screen updates would you like to take a screenshot for when recording? (Recommended is between 15-30, the lower the smoother the footage) ")

    return int(start_num), int(centre_mass), int(min_mass), int(max_mass), random_mass, asteroid_num, asteroid_dist, asteroid_belt_num, int(video_frame_rate), int(number_density)

if __name__ == "__main__":
    running = True

    print("\nGeneral Controls"
          "\n'P' to pause and unpause (The sim will start paused)."
          "\n\nTrail Controls"
          "\n'T' to reset the trails, "
          "\n'Y' to toggle trails on and off, "
          "\nUp and Down keys to change the minimum size for an object to produce trails. "
          "\n\nRecording Controls"
          "\n'C' to create a screenshot of the current screen, "
          "\n'M' to start making a step-frame movie (Then press M again to stop the recording).\n"
          "\nSize-Colour Key: 1." + "\033[38;2;255;255;255m" + '⬤' + "\033[38;2;160;160;160m  2." + "\033[38;2;255;255;220m" + '⬤' + "\033[38;2;160;160;160m  3." + "\033[38;2;255;245;200m" + '⬤' + "\033[38;2;160;160;160m  4." + "\033[38;2;255;230;190m" + '⬤' + "\033[38;2;160;160;160m  5." + "\033[38;2;255;210;160m" + '⬤' + "\033[38;2;160;160;160m  6." + "\033[38;2;255;190;140m" + '⬤' + "\033[38;2;160;160;160m  7." + "\033[38;2;255;160;120m" + '⬤' + "\033[38;2;160;160;160m  8." + "\033[38;2;255;130;110m" + '⬤' + "\033[38;2;160;160;160m  9." + "\033[38;2;255;100;90m" + '⬤' + "\033[38;2;160;160;160m  10+." + "\033[38;2;255;75;75m" + '⬤\033[38;2;160;160;160m \n'
          )

    user_text = ''
    start_num, centre_mass, min_mass, max_mass, random_mass, asteroid_num, asteroid_dist, asteroid_belt_num, video_frame_rate, number_density = startup()
    create_objects(start_num, centre_mass, min_mass, max_mass, random_mass, asteroid_num, asteroid_dist, asteroid_belt_num, number_density)

    is_paused = False
    first_pass = True
    show_trails = True
    recording = False
    movie_folder = "0"
    min_trail_radius = 1
    video_frame_num = 0
    time_since_update = 0
    times = []
    display_frame_rate = math.ceil(0.002 / G)
    current_frame = display_frame_rate

    if display_frame_rate > 50:
        display_frame_rate = 50

    current_movie_frame = video_frame_rate
    screen.set_colorkey((0, 0, 0))

    window = pygame.display.set_mode([win_width, win_height])
    grav_ratio = pygame.math.clamp(0.00001 / G, 0, 0.05)

    while running:

        if not is_paused:
            force_calc_num = 0
            current_frame += 1

            for obj in objects:
                detect_collisions(obj)

            for obj in to_remove:
                if obj in objects:
                    objects.remove(obj)
                    del obj

            to_remove = []

            for obj in objects:
                obj.frc = [0, 0]
                obj.force_calculated = False

            for obj in objects:
                calculate_total_force_vector(obj)
                if obj.can_move:
                    acceleration = [obj.frc[0] / obj.mass, obj.frc[1] / obj.mass]
                    obj.velocity = [obj.velocity[0] + acceleration[0], obj.velocity[1] + acceleration[1]]
                    obj.x += obj.velocity[0]
                    obj.y += obj.velocity[1]
                    #obj.zones = check_zones([obj.x, obj.y], obj.radius)

            if not first_pass:
                times.append(time.time() - time_since_update)

            if current_frame >= display_frame_rate:

                screen.fill((0, 0, 0))

                current_frame = 0
                current_movie_frame += 1
                if recording and current_movie_frame >= video_frame_rate:
                    current_movie_frame = 0
                    if not os.path.exists(r".\Movies"):
                        os.makedirs(r".\Movies")

                    pygame.image.save(window, r".\Movies\movie" + movie_folder + r"\screenshot" + str(video_frame_num) + ".jpg")
                    video_frame_num += 1

                largestMasses = [0, 0, 0]
                for obj in objects:

                    obj.draw(screen, trails, show_trails, min_trail_radius)

                    if obj.mass > largestMasses[0] and obj.can_move:
                        largestMasses[1] = largestMasses[0]
                        largestMasses[0] = obj.mass
                    elif obj.mass > largestMasses[1]:
                        largestMasses[2] = largestMasses[1]
                        largestMasses[1] = obj.mass
                    elif obj.mass > largestMasses[2]:
                        largestMasses[2] = obj.mass

                sm_text = small_text.render("Star Mass: " + str(objects[0].mass), False, (255, 255, 255))
                sm_text_pos = sm_text.get_rect(center=(win_width / 2, win_height * (2 / 100)))
                sm_text_pos.left = win_width * 1/100

                lb_text = small_text.render("Top 3 Massive Bodies:", False, (255, 255, 255))
                lb_text_pos = lb_text.get_rect(center=(win_width / 2, win_height * (5 / 100)))
                lb_text_pos.left = win_width * 1 / 100

                lb1_text = tiny_text.render("1. " + str(largestMasses[0]), False, (255, 255, 255))
                lb1_text_pos = lb1_text.get_rect(center=(win_width / 2, win_height * (8 / 100)))
                lb1_text_pos.left = win_width * 1 / 100

                lb2_text = tiny_text.render("2. " + str(largestMasses[1]), False, (255, 255, 255))
                lb2_text_pos = lb2_text.get_rect(center=(win_width / 2, win_height * (10 / 100)))
                lb2_text_pos.left = win_width * 1 / 100

                lb3_text = tiny_text.render("3. " + str(largestMasses[2]), False, (255, 255, 255))
                lb3_text_pos = lb3_text.get_rect(center=(win_width / 2, win_height * (12 / 100)))
                lb3_text_pos.left = win_width * 1 / 100

                mrt_text = tiny_text.render("Min radius to render trail: " + str(min_trail_radius), False, (255, 255, 255))
                mrt_text_pos = sm_text.get_rect(center=(win_width / 2, win_height * (98 / 100)))
                mrt_text_pos.left = win_width * 1 / 100

                blit_text(screen, sm_text, sm_text_pos)
                blit_text(screen, lb_text, lb_text_pos)
                blit_text(screen, lb1_text, lb1_text_pos)
                blit_text(screen, lb2_text, lb2_text_pos)
                blit_text(screen, lb3_text, lb3_text_pos)
                blit_text(screen, mrt_text, mrt_text_pos)
                window.blit(trails, (0, 0))
                window.blit(screen, (0, 0))

                pygame.display.update()


                if first_pass:
                    first_pass = False
                    is_paused = True

            time_since_update = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sum = 0
                for t in times:
                    sum += t
                pygame.quit()
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    trails.fill((0, 0, 0))

                if event.key == pygame.K_y:
                    show_trails = not show_trails

                if event.key == pygame.K_p:
                    is_paused = not is_paused

                if event.key == pygame.K_UP:
                    min_trail_radius += 1

                if event.key == pygame.K_DOWN:
                    min_trail_radius -= 1
                    if min_trail_radius < 1:
                        min_trail_radius = 1

                if event.key == pygame.K_c:

                    if not os.path.exists(r".\Screenshots"):
                        os.makedirs(r".\Screenshots")

                    path = r".\Screenshots"
                    list = []

                    for (root, dirs, file) in os.walk(path):
                        for f in file:
                            if "screenshot" in f:
                                list.append(f)

                    lastNum = "0"
                    for i in range(len(list)):
                        number = ""
                        for j in range(len(list[i])):
                            if j > 9:
                                if list[i][j].isdigit():
                                    number += list[i][j]
                                else:
                                    break

                        if int(number) > int(lastNum):
                            lastNum = number

                    screenShotNum = int(lastNum) + 1

                    pygame.image.save(window, r".\Screenshots\screenshot" + str(screenShotNum) + ".jpg")
                if event.key == pygame.K_m:
                    recording = not recording

                    if recording:

                        if not os.path.exists(r".\Movies"):
                            os.makedirs(r".\Movies")

                        path = r".\Movies"
                        list = []

                        for (root, dirs, file) in os.walk(path):
                            for d in dirs:
                                if "movie" in d:
                                    list.append(d)

                        lastNum = "0"
                        for i in range(len(list)):
                            number = ""
                            for j in range(len(list[i])):
                                if j > 4:
                                    number += list[i][j]

                            if int(number) > int(lastNum):
                                lastNum = number

                        movie_folder = str(int(lastNum) + 1)
                        if not os.path.exists(r".\Movies\movie" + movie_folder):
                            os.makedirs(r".\Movies\movie" + movie_folder)
                    else:
                        movieFrame = 10
                        movieFrameNum = 1