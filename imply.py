#!/usr/bin/env python

import cframe
import argparse
import os

J_Frontier = set()
D_Frontier = set()

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
                valid = imply_and_check(circ, faults, loc, val, D_drive, J_Frontier)
                if not valid:
                    print("CONFLICT. Commands aborted on command #%d\n" % count)
                    exit()

            # J Frontier command calls the 
            if command == cframe.Command.Jfront:
                report_j_front(circ, ofile, J_Frontier)

            # D Frontier command 
            if command == cframe.Command.Dfront:
                report_d_front(circ, ofile)

            # X path command
            if command == cframe.Command.Xpath:
                x_path_check(circ, ofile)

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

def is_J_Frontier(circuit, gate_obj):
    countx = 0
    inputs = []
    obj = set()

    if(gate_obj.value != cframe.Roth.X and gate_obj.gatetype != 'INPUT'):
      for fin in gate_obj.fanin:
         inputs.append(fin)
      for gate in circuit.gatemap.values(): 
         if(gate.name in inputs):
           obj.add(gate)

      for gate in obj:
         if(gate.value == cframe.Roth.X):
            countx += 1

      if(countx >= 2): 
         return True
      else:
         return False

    else:
      return False


def evaluate(gate_obj, circuit):
        """Evaluate current gate based on circuit state.

        Note that this function both updates the value of the current gate and
        returns the new value based on the evaluation.

        Args:
           ctk (Circuit): Circuit containing current gate and all fanin gates.

        Returns:
           Roth: Updated Roth value of current gate based on evaluation of 
              the fanin states.

        Raises:
           KeyError: If current gatetype is not in Gate.types.
        """

        #if gate_obj.gatetype not in Gate.types:
        #    raise KeyError("Invalid gate type")
            
        statein = (circuit.gatemap[fi].value for fi in gate_obj.fanin)

        if gate_obj.gatetype == "AND":
          #if(gate_obj.value == cframe.Roth.X):
            val = cframe.Roth.operate("AND", statein)
        if gate_obj.gatetype == "NAND":
          #if(gate_obj.value == cframe.Roth.X):
            val = cframe.Roth.invert(cframe.Roth.operate("AND", statein))
        if gate_obj.gatetype == "OR":
          #if(gate_obj.value == cframe.Roth.X):
            val = cframe.Roth.operate("OR", statein)
        if gate_obj.gatetype == "NOR":
          #if(gate_obj.value == cframe.Roth.X):
            val = cframe.Roth.invert(cframe.Roth.operate("OR", statein))
       # if self.gatetype == "XOR":
       #     self.value = Roth.operate("XOR", statein)
       # if self.gatetype == "XNOR":
       #     self.value = Roth.invert(Roth.operate("XOR", statein))
       # if self.gatetype == "BUFF":
       #     self.value = statein[0].value
       # if self.gatetype == "NOT":
       #     self.value = Roth.invert(self.value)
       # if self.gatetype == "DFF":   # DFF not supported at this time
       #     self.value = Roth.X
       # if self.gatetype == "UNDEFINED":
       #     self.value = Roth.X

        #logging.debug("GATE: eval\tname:%s\tinputs: %s\tresult: %s",
        #              self.name.rjust(6),
        #              str([s.name for s in statein]),
        #              self.value)
        return val     

def imply_and_check(circuit, faults, location, value, D_drive, J_Frontier):
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
       if(location == gate.name):
          name = gate.gatetype
          gate_obj = gate
          for fault in faults:
             if(gate.name != fault.stem): 
               if gate.value == cframe.Roth.X:
                 gate.value = value
               elif gate.value != value:
                 return False
               #print(gate.name, gate.gatetype, gate.value.value)

               if(is_J_Frontier(circuit, gate_obj)):
                 J_Frontier.add(gate_obj.name)
               else:
                 if(gate_obj.name in J_Frontier):
                   J_Frontier.remove(gate_obj.name)
             else:
                
                  #print("Inside imply fault")
                  if(location == fault.stem):
                    if(value != fault.value):
                      if(fault.value == cframe.Roth.One and value == cframe.Roth.Zero):
                        fault.value = cframe.Roth.D_b
                        gate_obj.value = cframe.Roth.D_b
                    else:
                        fault.value = cframe.Roth.D
                        gate_obj.value = cframe.Roth.D
                  print(fault.stem, fault.value, gate_obj.value)

                  if(is_J_Frontier(circuit, gate_obj)):
                    J_Frontier.add(gate_obj.name)
                  else:
                    if(gate_obj.name in J_Frontier):
                      J_Frontier.remove(gate_obj.name)
               

    rothv = value 

    if(location in circuit.inputs): 
       for gate in circuit.gatemap.values():
         if location in gate.fanin:
            if(rothv == find_cval(name)):
              loc = gate.name
              #val = get_val(rothv, gate.gatetype)
              val = evaluate(gate, circuit)
            else:
              loc = gate.name
              #for item in gate.fanin:
                 #inputs.append(circuit.gatemap[item].value())
              #  for key, val in circuit.gatemap.items():
              #      if(key == item and key != location):
              #        temp = val.value
              #        inputs.append(temp)
              #inputs.append(gate_obj.value.value)
              #print(input
              #print(inputs, gate.gatetype)
              val =  evaluate(gate, circuit)
              #print(gate.name)
              #print(val, val.value)
            if(val != cframe.Roth.X):  
              imply_and_check(circuit, faults, loc, val, D_drive, J_Frontier)   
               
    elif(location in circuit.outputs): 
        for fault in faults:
         if(location != fault.stem):
           temp = find_cval(gate_obj.gatetype)
           if((gate_obj.gatetype == 'NAND' or gate_obj.gatetype == 'NOR') and (gate_obj.value == temp)):
              for fin in gate.fanin:  
                loc = fin
                val = cframe.Roth.invert(temp)
                imply_and_check(circuit, faults, loc, val, D_drive)
           elif((gate_obj.gatetype == 'AND' or gate_obj.gatetype == 'OR') and (gate_obj.value == cframe.Roth.invert(temp))):
               for fin in gate.fanin:  
                loc = fin
                val = cframe.Roth.invert(temp)
                imply_and_check(circuit, faults, loc, val, D_drive)
          
  
    else:
       for gate in circuit.gatemap.values():
          if location in gate.fanin:
            loc = gate.name
            val = evaluate(gate, circuit)
            imply_and_check(circuit, faults, loc, val, D_drive, J_Frontier)

       #for gate in gate_obj.fanin:
          #inputs.append(circuit.gatemap[gate].value)

       for fault in faults:
         if(location != fault.stem):
           temp = find_cval(gate_obj.gatetype)
           if((gate_obj.gatetype == 'NAND' or gate_obj.gatetype == 'NOR') and (gate_obj.value == temp)):
              for fin in gate.fanin:  
                loc = fin
                val = cframe.Roth.invert(temp)
                imply_and_check(circuit, faults, loc, val, D_drive)
           elif((gate_obj.gatetype == 'AND' or gate_obj.gatetype == 'OR') and (gate_obj.value == cframe.Roth.invert(temp))):
               for fin in gate.fanin:  
                loc = fin
                val = cframe.Roth.invert(temp)
                imply_and_check(circuit, faults, loc, val, D_drive)
              

      # check_gate_out = gate_out(gate_obj.gatetype, inputs)
      # cval = find_cval(gate_obj.gatetype)
      # if(value == cval and value != (cframe.Roth.D or cframe.Roth.D_b or cframe.Roth.X)):
      #    val = cframe.Roth.invert(cval)
      #    for item in gate_obj.fanin:
      #       imply_and_check(circuit, faults, item, val, D_drive, J_Frontier)
      # if(value == cval and  check_gate_out != (cframe.Roth.D or cframe.Roth.D_b or cframe.Roth.X)):
      #   if check_gate_out != value:
      #        return False
    
    

    # True indicates valid implication; False indicates a conflict
    return True


def report_j_front(circuit, outfile, J_Frontier):
    """Determine the gates on the J frontier and write out to output file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """
    outfile.write("J-Frontier\n")
    if(J_Frontier):
      for item in J_Frontier:
         outfile.write(item + "\n")
    outfile.write("$\n") 
     


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
