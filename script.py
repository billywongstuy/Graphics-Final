import mdl
from display import *
from matrix import *
from draw import *

"""======== first_pass( commands, symbols ) ==========

  Checks the commands array for any animation commands
  (frames, basename, vary)
  
  Should set num_frames and basename if the frames 
  or basename commands are present

  If vary is found, but frames is not, the entire
  program should exit.

  If frames is found, but basename is not, set name
  to some default value, and print out a message
  with the name being used.

  jdyrlandweaver
  ==================== """
def first_pass( commands ):

    frameCheck = varyCheck = nameCheck = False
    name = ''
    num_frames = 1
    
    for command in commands:
        
        if command[0] == 'frames':
            num_frames = command[1]
            frameCheck = True
        elif command[0] == 'vary':
            varyCheck = True
        elif command[0] == 'basename':
            name = command[1]
            nameCheck = True

    if varyCheck and not frameCheck:
        print 'Error: Vary command found without setting number of frames!'
        exit()

    elif frameCheck and not nameCheck:
        print 'Animation code present but basename was not set. Using "frame" as basename.'
        name = 'frame'
    
    return (name, num_frames)


"""===================  half_pass ============
For lighting for shading
====================="""

def half_pass(commands):
    lights = {}
    ambient = [255,255,255]
    constants = {}
    shading = 'flat'
    for command in commands:
        if command[0] == 'light':
            r = command[0]
            g = command[1]
            b = command[2]
            x = command[3]
            y = command[4]
            z = command[5]
            lights[x,y,z] = [r,g,b]
        if command[0] == 'ambient':
            ambient = [command[0], command[1], command[2]]
        if command[0] == 'constants':
            name = command[0]
            if command[10] != None:
                constants[name] = [command[1],command[2],command[3],command[4],command[5],command[6],command[7],command[8],command[9],command[10],command[11],command[12]]
            else:
                constants[name] = [command[1],command[2],command[3],command[4],command[5],command[6],command[7],command[8],command[9],0,0,0]
        if command[0] == 'shading':
            shading = command[1]
    return (lights,ambient,constants,shading)

"""======== second_pass( commands ) ==========

  In order to set the knobs for animation, we need to keep
  a seaprate value for each knob for each frame. We can do
  this by using an array of dictionaries. Each array index
  will correspond to a frame (eg. knobs[0] would be the first
  frame, knobs[2] would be the 3rd frame and so on).

  Each index should contain a dictionary of knob values, each
  key will be a knob name, and each value will be the knob's
  value for that frame.

  Go through the command array, and when you find vary, go 
  from knobs[0] to knobs[frames-1] and add (or modify) the
  dictionary corresponding to the given knob with the
  appropirate value. 
  ===================="""
def second_pass( commands, num_frames ):
    frames = [ {} for i in range(num_frames) ]

    for command in commands:
        if command[0] == 'vary':
            knob_name = command[1]
            start_frame = command[2]
            end_frame = command[3]
            start_value = float(command[4])
            end_value = float(command[5])
            value = 0
            
            if ((start_frame < 0) or
                (end_frame >= num_frames) or
                (end_frame <= start_frame)):
                print 'Invalid vary command for knob: ' + knob_name
                exit()

            delta = (end_value - start_value) / (end_frame - start_frame)

            for f in range(num_frames):            
                if f == start_frame:
                    value = start_value
                    frames[f][knob_name] = value
                elif f >= start_frame and f <= end_frame:
                    value = start_value + delta * (f - start_frame)
                    frames[f][knob_name] = value
                #print 'knob: ' + knob_name + '\tvalue: ' + str(frames[f][knob_name])
    return frames

def run(filename):
    """
    This function runs an mdl script
    """
    color = [0, 0, 0]
    tmp = new_matrix()
    ident( tmp )

    p = mdl.parseFile(filename)

    if p:
        (commands, symbols) = p
    else:
        print "Parsing failed."
        return

    (name, num_frames) = first_pass(commands)
    (lights,ambient,constants,shading) = half_pass(commands)

    setting = {}
    setting['lights'] = lights
    setting['ambient'] = ambient
    setting['shading'] = shading
    setting['constants'] = constants
    
    frames = second_pass(commands, num_frames)
    #print frames
    step = 0.1

    #print symbols

    for f in range(num_frames):

        tmp = new_matrix()
        ident(tmp)
        stack = [ [x[:] for x in tmp] ]
        screen = new_screen()
        zb = new_zbuffer()
        tmp = []

        #Set symbol values for multiple frames
        if num_frames > 1:
            frame = frames[f]
            for knob in frame:
                symbols[knob][1] = frame[knob]
                #print '\tkob: ' + knob + '\tvalue: ' + str(frame[knob])
                
        for command in commands:
            #print command
            c = command[0]
            args = command[1:]
            knob_value = 1

            if c == 'set':
                symbols[args[0]][1] = args[1]
            elif c == 'set_knobs':
                for knob in symbols:
                    if symbols[knob][0] == 'knob':
                        symbols[knob][1] = args[0]
            elif c == 'box':
                add_box(tmp,
                        args[0], args[1], args[2],
                        args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zb, color)
                tmp = []
            elif c == 'sphere':
                add_sphere(tmp,
                           args[0], args[1], args[2], args[3], step)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zb, color)
                tmp = []
            elif c == 'torus':
                add_torus(tmp,
                          args[0], args[1], args[2], args[3], args[4], step)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zb, color)
                tmp = []
            elif c == 'move':
                if command[-1]:
                    knob_value = symbols[command[-1]][1]
                tmp = make_translate(args[0] * knob_value, args[1] * knob_value, args[2] * knob_value)
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'scale':
                if command[-1]:
                    knob_value = symbols[command[-1]][1]                
                tmp = make_scale(args[0] * knob_value, args[1] * knob_value, args[2] * knob_value)
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'rotate':
                if command[-1]:
                    knob_value = symbols[command[-1]][1]
                    
                theta = args[1] * (math.pi/180) * knob_value
                if args[0] == 'x':
                    tmp = make_rotX(theta)
                elif args[0] == 'y':
                    tmp = make_rotY(theta)
                else:
                    tmp = make_rotZ(theta)
                matrix_mult( stack[-1], tmp )
                stack[-1] = [ x[:] for x in tmp]
                tmp = []
            elif c == 'push':
                stack.append([x[:] for x in stack[-1]] )
            elif c == 'pop':
                stack.pop()
            elif c == 'display':
                display(screen)
            elif c == 'save':
                save_extension(screen, args[0])
        
        if num_frames > 1:
            fname = 'anim/%s%03d.png' % (name, f)
            print 'Saving frame: ' + fname
            save_extension( screen, fname )

    if num_frames > 1:
        make_animation(name)
    
