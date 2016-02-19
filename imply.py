#!/usr/bin/env python

import cframe
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="Perform implication and checking for an ISCAS circuit.")
    parser.add_argument("circuit", help="ISCAS file describing circuit to be collapsed")
    parser.add_argument("commands", help="Command file describing the commands to be applied")
    parser.add_argument("outfile", help="Base name for output files generated")
    parser.add_argument("-u", help="Enable unique D-drive", default=False, action='store_true')

    args = parser.parse_args()

    # Load circuit
    circ = cframe.Circuit(args.circuit)

    # Print circuit stats
    circ.print_summary()

    # Fault list
    faults = []

    # Unique D-drive flag
    D_drive = args.u
  

    # Open results file
    with open(args.outfile+".result", "w+") as ofile:

        # Read commands from file and process them
        for count, command_tuple in enumerate(cframe.Command.read_commands(args.commands)):
            command = command_tuple[0]

            # Faults are added to the fault list (used by imply_and_check routine)
            # Fault command, comm_tuple = (Command, gatename, value)
            if command == cframe.Command.Fault:
                loc = command_tuple[1] # location (gatename)
                val = command_tuple[2] # value (Roth) (One or Zero)
                faults.append(cframe.Fault(val, loc))
        
            # Implications call the imply_and_check routine and abort on conflict
            # Imply command, comm_tuple = (Command, gatename, value)
            if command == cframe.Command.Imply:
                loc = command_tuple[1] # location (gatename)
                val = command_tuple[2] # value (Roth)
                valid = imply_and_check(circ, faults, loc, val, D_drive)
                if not valid:
                    print("CONFLICT. Commands aborted on command #%d\n" % count)
                    exit()

            # J Frontier command calls the 
            if command == cframe.Command.Jfront:
                report_j_front(circ, ofile)

            # D Frontier command 
            if command == cframe.Command.Dfront:
                report_d_front(circ, ofile)

            # X path command
            if command == cframe.Command.Xpath:
                x_path_check(circ)

            # Display command
            if command == cframe.Command.Display:
                circ.write_state(ofile)

def find_cval(name): #Returns controlling value of the gate
    if(name == 'AND' or name == 'NAND'):
       return cframe.Roth.Zero
    elif(name == 'OR' or name == 'NOR'):
       return cframe.Roth.One
    else:
       return -1 #Controlling value not defined

def get_val(cval, name): #Gate output if input is a controlling value
    if(name == 'AND' and cval == cframe.Roth.Zero):
       return cframe.Roth.Zero
    elif(name == 'NAND' and cval == cframe.Roth.Zero):
       return cframe.Roth.One
    elif(name == 'OR' and cval == cframe.Roth.One):
       return cframe.Roth.One
    elif(name == 'NOR' and cval == cframe.Roth.One):
       return cframe.Roth.Zero
    else:
       return -1 #not defined



def gate_out(inputs,optype): #Returns controlling value of the gate 

    if optype == 'AND': 
       return cframe.Roth.operate('AND',inputs) 
    elif optype == 'NAND':
       return cframe.Roth.invert(cframe.Roth.operate('AND',inputs)) 
    elif optype == 'OR':
       return cframe.Roth.operate('OR',inputs)
    elif optype == 'NOR': 
       return cframe.Roth.invert(cframe.Roth.operate('OR',inputs))
    elif optype == 'XOR':
       return cframe.Roth.operate('XOR',inputs)
    elif optype == 'XNOR':
       return cframe.Roth.invert(cframe.Roth.operate('XOR',inputs))
    else:
       return -1 #value not defined



def imply_and_check(circuit, faults, location, value, D_drive):
    """Imply a value and check for consequences in a circuit.

    Args:
       circuit (Circuit): The circuit under consideration.
       faults (list): A list of active Fault objects in the circuit.
       location (str): The string name of the gate location of the implication.
       value (Roth): A Roth object representing the value implied.
       D_drive (bool): Flag indicating whether to use unique D-drive.

    Returns:
       bool: A boolean indicating whether the implication is valid.
    """
    name = ""
    inp_list = []
    inputs = []

    for gate in circuit.gatemap.values():
       if location == gate.name:
         name = gate.gatetype

       if gate.value == cframe.Roth.X:
         gate.value = value
       elif gate.value != value:
         return "Failure"
       else:
         gate.value = value

    rothv = value
    for gate in circuit.gatemap.values():
       if(location in circuit.inputs and location in gate.fanin):
         if(rothv == find_cval(name)):
           loc = gate.name
           val = get_val(rothv, gate.gatetype)
         else:
           loc = gate.name
           for item in gate.inputs:
              if item != location:
                inputs.append(item)
           inputs.append(location)
           val =  gate_out(inputs, gate.gatetype)

         #if val != gate.value:
          # return "Failure" 
           
         for Fault in faults:
           if loc == Fault.stem:
             if val != Fault.value:
               if val == cframe.Roth.One and Fault.value == cframe.Roth.Zero:
                 val = cframe.Roth.D  
               else:
                 val = cframe.Roth.D_b
    
       else:
         

        
         imply_and_check(circuit, faults, loc, val, D_drive)  
             #imply_list[gate.name] = val 
         #if imply_list[gate.name] != val:
           #return False
              
               #if(imply_and_check(circ,faults,loc,val, D_drive)):
               #   imply_list[loc] = val
               #else:
               #   return False 
       else: 
         for item in gate.fanin:
           inp_list.append(imply_list[item])
         loc = gate.name
         val = gate_out(gate.gatetype, inp_list)
               #if(imply_and_check(circ, faults, loc, val, D_drive)):
               #  imply_list[loc] = val
               #else  
               #  return False                   
         if loc == Fault.stem:
           if val != Fault.value: 
             if val == cframe.Roth.One and Fault.value == cframe.Roth.Zero:
               val = cframe.Roth.D
             else:
               val = cframe.Roth.D_b 
           imply_list[gate.name] = val
         else:
           if imply_list[gate.name] != val:
             return False
                  
                    
                    
               

               
              
             
      
    
    
    
    #print("TODO: Complete this function to imply and check a value.")

    # True indicates valid implication; False indicates a conflict
    return True


def report_j_front(circuit, outfile):
    """Determine the gates on the J frontier and write out to output file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """

    #print("TODO: Complete this function to identify and report the J frontier gates.")


def report_d_front(circuit, outfile):
    """Determine the gates on the D frontier and write out to output file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """

    #print("TODO: Complete this function to identify and report the D frontier gates.")


def x_path_check(circuit, outfile):
    """Determine for each gate on the D frontier if an X-path exists and write to output
    file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """

    #print("TODO: Complete this function to identify and report the D frontier gates with X-paths.")


if __name__ == '__main__':

    # Open logging file
    logfile = os.path.join(os.path.dirname(__file__), "logs/imply.log")
    cframe.logging.basicConfig(filename=logfile,
                               format='%(asctime)s %(message)s',
                               datefmt='%m/%d/%Y %I:%M:%S %p',
                               level=cframe.logging.DEBUG)

    main()
