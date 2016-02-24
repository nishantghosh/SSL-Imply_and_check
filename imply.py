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
                x_path_check(circ, ofile)

            # Display command
            if command == cframe.Command.Display:
                circ.write_state(ofile)

def find_cval(name):
    """
    Evaluates controlling value of the gate
    Args: 
    name (Gate.gatetype) : Type of gate

    Returns:
    Roth object that is controlling value of the gate
    """ 
    if(name == 'AND' or name == 'NAND'):
       return cframe.Roth.Zero
    elif(name == 'OR' or name == 'NOR'):
       return cframe.Roth.One
    else:
       return -1 #Controlling value not defined

def get_val(cval, name):
    """
    Evaluates gate output if input is a controlling value
   
    Args:
    cval : Controlling value of the gate type
    name (Gate.gatetype) : Type of gate

    Returns:
    Result of applying controlling value at any input of the gate
    """ 
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


def is_J_Frontier(circuit):
    """
    Adds gates on the J_Frontier to a set
   
    Args:
    circuit (Circuit): Circuit containing current gate and all fanin gates.
    
    Returns:
    Set of gate names on the J-Frontier
    """ 
    countx = 0
    inputs = []
    obj = set()
    for gate in circuit.gatemap.values():
       countx = 0
       if(gate.value != cframe.Roth.X and gate.gatetype != 'INPUT' and gate.value != evaluate(gate, circuit)): #Check if gate does not have a value implied by inputs, 
         for fin in gate.fanin:                                                                                #Check if at least two inputs are unknown
           if(circuit.gatemap[fin].value == cframe.Roth.X):
             countx += 1
         if(countx >= 2): 
           obj.add(gate.name)
      
    return obj  
    
def is_D_Frontier(circuit):
    """
    Adds gates on the D_Frontier to a set
   
    Args:
    circuit (Circuit): Circuit containing current gate and all fanin gates.
    
    Returns:
    Set of gate names on the D-Frontier
    """
    countx = 0
    inputs = []
    obj = set()
    for gate in circuit.gatemap.values():
       countx = 0
       if(gate.value == cframe.Roth.X and gate.gatetype != 'INPUT'):    #Check if output is unknown, gate is not an input line. 
         for fin in gate.fanin: 
           if(circuit.gatemap[fin].value == cframe.Roth.D or circuit.gatemap[fin].value == cframe.Roth.D_b): #Check if at least one input is a D/D_b
             countx += 1
         if(countx >= 1): 
           obj.add(gate.name)
      
    return obj  

  
def evaluate(gate_obj, circuit):
        """Evaluate current gate based on circuit state.

        
        Args:
           circuit (Circuit): Circuit containing current gate and all fanin gates.
           gate_obj (Gate object): Gate object to evaluate

        Returns:
           Roth: Updated Roth value of current gate based on evaluation of 
              the fanin states.
           DOES NOT UPDATE VALUE OF GATE!

        """

        statein = (circuit.gatemap[fi].value for fi in gate_obj.fanin)

        if gate_obj.gatetype == "AND":
          
            val = cframe.Roth.operate("AND", statein)
        if gate_obj.gatetype == "NAND":
          
            val = cframe.Roth.invert(cframe.Roth.operate("AND", statein))
        if gate_obj.gatetype == "OR":
          
            val = cframe.Roth.operate("OR", statein)
        if gate_obj.gatetype == "NOR":
          
            val = cframe.Roth.invert(cframe.Roth.operate("OR", statein))
        if gate_obj.gatetype == "XOR":
            val = cframe.Roth.operate("XOR", statein)
        if gate_obj.gatetype == "XNOR":
            val = cframe.Roth.invert(Roth.operate("XOR", statein))
        if gate_obj.gatetype == "BUFF":
            val = statein[0].value
        if gate_obj.gatetype == "NOT":
            val = cframe.Roth.invert(circuit.gatemap[gate_obj.fanin[0]].value)
        
        return val     


def check_gate_in(circuit, gate_obj):
   """
   Checks if all but one input of the gate is unknown. Evaluates value to be implied to that location if any.
  
   Args:
   circuit (Circuit): Circuit containing current gate and all fanin gates.
   gate_obj : Gate object

   Returns:
   loc : location of the input on the circuit 
   val : Value to be implied
   """
   input_list = gate_obj.fanin 
   total_inputs = len(input_list)
   count = 0
   cval_flag = False 

   
   
   
   for fin in gate_obj.fanin:
      if(circuit.gatemap[fin].value == cframe.Roth.X):
        count += 1 
        inp = fin
        
      if(circuit.gatemap[fin].value == find_cval(gate_obj.gatetype) or circuit.gatemap[fin].value == cframe.Roth.D or circuit.gatemap[fin].value == cframe.Roth.D_b):
        cval_flag = True
      
   
   
   if(not cval_flag):
     if(count == 1):
       val = find_cval(gate_obj.gatetype)
       loc = inp
       
       return(val, loc)
     else:
       val = cframe.Roth.X
       loc = "NONE"
       return(val, loc)
   else:
     val = cframe.Roth.X
     loc = "NONE"
     
     return(val, loc)  

   
   


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
    global J_Frontier
    """
    Routine that implies values to a line/fault by checking previous value on the line/fault.
    Returns False if there is a conflict
    """
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
               
             else:
                   
                  if(location == fault.stem):
                    if(value != fault.value):
                      if(fault.value == cframe.Roth.One and value == cframe.Roth.Zero):
                        fault.value = cframe.Roth.D_b
                        gate_obj.value = cframe.Roth.D_b
                      elif(fault.value == cframe.Roth.Zero and value == cframe.Roth.One):
                        fault.value = cframe.Roth.D
                        gate_obj.value = cframe.Roth.D
                      else:
                        return False
                 
               

    rothv = value 
    """
    Check if current gate is an INPUT line/OUTPUT line/Internmediate net 
    Does forward implication, backward implication or both depending on location in circuit
    Calls imply_and_check() recurcsively on locations with imply values
    """
    if(location in circuit.inputs): 
       for gate in circuit.gatemap.values():
         if location in gate.fanin:
            if(gate.value == cframe.Roth.X):
              loc = gate.name 
              val = evaluate(gate, circuit)
            else:
              loc = gate.name
              val =  evaluate(gate, circuit)

            if(val != cframe.Roth.X):  
              imply_and_check(circuit, faults, loc, val, D_drive)
            
                              
              
    elif(location in circuit.outputs): 
        for fault in faults:
         if(location != fault.stem):
           temp = find_cval(gate_obj.gatetype)
           if((gate_obj.gatetype == 'NAND' or gate_obj.gatetype == 'NOR') and (gate_obj.value == temp)):
              for fin in gate_obj.fanin:  
                loc = fin
                val = cframe.Roth.invert(temp)
                imply_and_check(circuit, faults, loc, val, D_drive)
           elif((gate_obj.gatetype == 'AND' or gate_obj.gatetype == 'OR') and (gate_obj.value == cframe.Roth.invert(temp))):
               for fin in gate_obj.fanin:  
                loc = fin
                val = cframe.Roth.invert(temp)
                imply_and_check(circuit, faults, loc, val, D_drive)

               
          
    else:
       for gate in circuit.gatemap.values():
          if location in gate.fanin: 
            temp1 = find_cval(gate.gatetype) 
            if(gate.gatetype == 'NAND' or gate.gatetype == 'NOR'):
             if(gate.value == temp1 and gate.value != cframe.Roth.X):
               
               for fin in gate.fanin:  
                 loc = fin
                 val = cframe.Roth.invert(temp1)
                 imply_and_check(circuit, faults, loc, val, D_drive)
             elif(gate.value == cframe.Roth.invert(temp1) and gate.value != cframe.Roth.X):
               
               (val, loc) = check_gate_in(circuit, gate)
               if(val == find_cval(gate_obj.gatetype) and loc != "NONE"):
                 imply_and_check(circuit, faults, loc, val, D_drive)
             else:
               loc = gate.name
               val = evaluate(gate, circuit)
               imply_and_check(circuit,faults,loc,val,D_drive)

            elif(gate.gatetype == 'AND' or gate.gatetype == 'OR'):
             if(gate.value == cframe.Roth.invert(temp1)): 
               for fin in gate.fanin:  
                loc = fin
                val = cframe.Roth.invert(temp1)
                imply_and_check(circuit, faults, loc, val, D_drive)
             elif(gate.value == cframe.Roth.invert(temp1) and gate.value != cframe.Roth.X):
               (val, loc) = check_gate_in(circuit, gate_obj)
               if(val == find_cval(gate_obj.gatetype) and loc != "NONE"):
                 imply_and_check(circuit, faults, loc, val, D_drive)
             else:
               loc = gate.name
               val = evaluate(gate, circuit)
               imply_and_check(circuit, faults, loc, val, D_drive)

            elif(gate.gatetype == 'NOT'):
                
                loc = gate.name
                val = evaluate(gate, circuit) 
                imply_and_check(circuit, faults, loc, val, D_drive)
 
       
       for fault in faults:
         if(location != fault.stem):
           temp = find_cval(gate_obj.gatetype)
           
           if(gate_obj.gatetype == 'NAND' or gate_obj.gatetype == 'NOR'):
             if(gate_obj.value == temp):
               
               for fin in gate_obj.fanin:  
                 loc = fin
                 val = cframe.Roth.invert(temp)
                 
                 
                 if(fin in circuit.inputs):
                   circuit.gatemap[fin].value = val
                 else:
                   imply_and_check(circuit, faults, loc, val, D_drive)
             else: 
               (val, loc) = check_gate_in(circuit, gate_obj)
               if(val == find_cval(gate_obj.gatetype) and loc != "NONE"):
                 imply_and_check(circuit, faults, loc, val, D_drive)
                    
           elif(gate_obj.gatetype == 'AND' or gate_obj.gatetype == 'OR'):
             if(gate_obj.value == cframe.Roth.invert(temp)): 
               for fin in gate.fanin:  
                loc = fin
                val = cframe.Roth.invert(temp)
                imply_and_check(circuit, faults, loc, val, D_drive)
             else:
               (val, loc) = check_gate_in(circuit, gate_obj)
               if(val == find_cval(gate_obj.gatetype) and loc != "NONE"):
                 imply_and_check(circuit, faults, loc, val, D_drive)

    
    # True indicates valid implication; False indicates a conflict
    
    return True


def report_j_front(circuit, outfile):
    
    """Determine the gates on the J frontier and write out to output file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """
    J = is_J_Frontier(circuit)
    outfile.write("J-Frontier\n") 
    if(J):
      for item in J:
         outfile.write(item + "\n")
    outfile.write("$\n\n") 
     


def report_d_front(circuit, outfile):
    
    """Determine the gates on the D frontier and write out to output file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """
    D = is_D_Frontier(circuit)
    outfile.write("D-Frontier\n")
    if(D):
      for item in D:
         outfile.write(item + "\n")
    outfile.write("$\n\n")
  


def x_path_check(circuit, outfile):
    """Determine for each gate on the D frontier if an X-path exists and write to output
    file.

    Args:
       circuit (Circuit): The circuit under consideration.
       outfile (file pointer): Open file pointer for writing.
    """
    
    D = is_D_Frontier(circuit)
    outfile.write("X-PATH\n") 
    if(D):
      for item in D:
         if(item in circuit.outputs):
           outfile.write(item + "\n")
         else:
           gate = circuit.gatemap[item]
           flag = True
           while not gate.name in circuit.outputs:  #Propagate till the gate is an OUTPUT line
              for i in circuit.gatemap.values():
                 if(gate.name in i.fanin):
                    gate = i
                 if gate.value != cframe.Roth.X:
                    flag = False               
                 else:
                    flag = True
           if(flag):                                #If the OUTPUT line is unknown, the gate is on X-PATH 
             outfile.write(item + "\n")
    outfile.write("$\n\n")
     

if __name__ == '__main__':

    # Open logging file
    logfile = os.path.join(os.path.dirname(__file__), "logs/imply.log")
    cframe.logging.basicConfig(filename=logfile,
                               format='%(asctime)s %(message)s',
                               datefmt='%m/%d/%Y %I:%M:%S %p',
                               level=cframe.logging.DEBUG)

    main()
