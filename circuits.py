"""Class to handle logical qubits for the Steane and Bacon Shor code"""

#import numpy as np
#from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute, Aer
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister


class SteaneCodeLogicalQubit(QuantumCircuit):
    """Generates the gates for one or two logical Qubits of the Steane code

        Parameters
        ----------
        d : int
            Number of logical "data" qubits to be initialised. Should be either 1 or 2 at present.
        parity_check_matrix : list
            Holds the parity check matrix from which the gates will be constructed.
        codewords : list
            Valid codewords for the Steane code
        extend_ancilla : bool 
            True if need to add extra ancilla for error correction without using MCT gates

        Notes
        -----
        Uses super to inherit methods from parent.
        """

    def __init__(self, d, parity_check_matrix, codewords, extend_ancilla = False):
        """Initialise qubit"""
        self.__extend_ancilla = extend_ancilla
        if self.__extend_ancilla:
            if d > 1:
                raise ValueError("Can't set up extra ancilla with two logical qubits due to memory size restrictions")
        self.__parity_check_matrix = parity_check_matrix
        self.__codewords = codewords
        self.define_data()
        list_of_all_registers = self.define_registers(d)
        # extend quantum circuits
        super().__init__(*list_of_all_registers)
        self.validate_parity_matrix()

    def define_data(self):
        """define standing data"""

        self.__num_data = 7             #seven data qubits for the Steane code
        self.__num_ancilla = 3          #six ancilla qubits, three x and three z
        if self.__extend_ancilla:   
            self.__num_extra_ancilla = 4       #four extra ancilla for decoding
        else:
            self.__num_extra_ancilla = 0   

        self.__data = []
        self.__mx = []
        self.__mz = []
        if self.__extend_ancilla: 
            self.__extra_ancilla = []
        self.__data_classical = []
        self.__mx_classical = []
        self.__mz_classical = []
        if self.__extend_ancilla:   
            self.__extra_ancilla_classical = []

    def define_registers(self, d):
        """Set up registers used based on number of logical qubits and whether error checking is needed.

        Parameters
        ----------
        d : int
            Number of the logical "data" qubits to be initialised. Should be either 0 or 1 at present.

        Notes
        -----
        The registers are stored in a list so that they can be indexed to simplify subsequent code.
        The registers required depends on the number of logical qubits and whether extra ancilla qubits
        are needed for error checking.
        """
        list_of_all_registers = []
        for index in range (d):  
            self.__qubit_no = str(index)
            # Quantum registers
            self.__data.append(QuantumRegister(self.__num_data, "data " + self.__qubit_no))
            self.__mx.append(QuantumRegister(self.__num_ancilla, "ancilla_X " + self.__qubit_no))
            self.__mz.append(QuantumRegister(self.__num_ancilla, "ancilla_Z " + self.__qubit_no))
            list_of_all_registers.append(self.__data[index])
            list_of_all_registers.append(self.__mx[index])
            list_of_all_registers.append(self.__mz[index])
            if self.__extend_ancilla: 
                self.__extra_ancilla.append(QuantumRegister(self.__num_extra_ancilla, name="extra_ancilla" + self.__qubit_no)) 
                list_of_all_registers.append(self.__extra_ancilla[index])
            # Classical registers
            self.__data_classical.append(ClassicalRegister(self.__num_data, "measure_data " + self.__qubit_no))
            self.__mx_classical.append(ClassicalRegister(self.__num_ancilla, "measure_ancilla_X " + self.__qubit_no))
            self.__mz_classical.append(ClassicalRegister(self.__num_ancilla, "measure_ancilla_Z " + self.__qubit_no))
            list_of_all_registers.append(self.__data_classical[index])
            list_of_all_registers.append(self.__mx_classical[index]) 
            list_of_all_registers.append(self.__mz_classical[index])
            #if self.__correct_errors:
            if self.__extend_ancilla: 
                self.__extra_ancilla_classical.append(
                    ClassicalRegister(self.__num_extra_ancilla, "measure_extra_ancilla " + self.__qubit_no))
                list_of_all_registers.append(self.__extra_ancilla_classical[index]) 
        return (list_of_all_registers)
    
    def validate_parity_matrix(self):
        """Validate the parity matrix against the allowed codewords"""
        if self.__parity_check_matrix == []:
            raise ValueError('Parity check matrix must be specified')
        
        for parity_row in self.__parity_check_matrix:
            if len(parity_row) != self.__num_data:
                raise ValueError('Parity check matrix rows incorrect length')

        for codeword_row in self.__codewords:
            if len(codeword_row) != self.__num_data:
                raise ValueError("Code word rows incorrect length")
            for parity_row in self.__parity_check_matrix:
                bit_store = False
                for codeword_bit in codeword_row:
                    if codeword_bit not in [0,1]:
                        raise ValueError("Code word entries must be 0 or 1")
                    for parity_bit in parity_row:
                        if parity_bit not in [0,1]:
                            raise ValueError("Parity matrix entries must be 0 or 1")
                        bit_store = bit_store ^ (bool(codeword_bit) ^ bool(parity_bit))
                if bit_store:
                    raise ValueError("Code word rows must be orthogonal to the parity matrix")

    def set_up_logical_zero(self, logical_qubit = 0):
        """Set up logical zero for data qubit

        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to initialise. Should be either 0 or 1 at present.
        """
        self._validate_logical_qubit_number(logical_qubit)
        
        parity_matrix_totals = [ 0 for x in range(self.__num_data)] # define an empty list ready to work out parity_matrix_totals

        for parity_row in self.__parity_check_matrix:
            for index in range(self.__num_data):
                parity_matrix_totals[index] = parity_matrix_totals[index] + parity_row[index]
        count = 0

        for index in range (self.__num_data):
            self.reset(self.__data[logical_qubit][index])

        for index in range (self.__num_data):
            #specify that each bit is zero
            if parity_matrix_totals[index] == 1:
                count = count + 1
                self.h(self.__data[logical_qubit][index])
                for parity_row in self.__parity_check_matrix:
                    if parity_row[index] == 1:              #correct row to build ancilla from
                        for column_number in range(self.__num_data):
                            if column_number != index:
                                if parity_row[column_number] == 1:
                                    self.cx(self.__data[logical_qubit][index],self.__data[logical_qubit][column_number])

        if count != self.__num_ancilla:
            raise ValueError('Unable to construct matrix as parity matrix does not match the ancilla needed')   

    def force_X_error(self, physical_qubit, logical_qubit = 0):
        """ Introduce an X error on one physical qubit

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to force error on. Should be either 0 or 1 at present.
            physical_qubit : int
                Number of qubit to force X error on.
        """
        self._validate_physical_qubit_number(physical_qubit)
        self._validate_logical_qubit_number(logical_qubit)
        self.x(self.__data[logical_qubit][physical_qubit])

    def force_Z_error(self, physical_qubit, logical_qubit = 0):
        """ Introduce Z error on one physical qubit

            Parameters
            ---------- 
            logical_qubit: int
                Number of the logical "data" qubits to force error on. Should be either 0 or 1 at present.
            physical_qubit : int
                Number of qubit to force Z error on.
        """
        self._validate_physical_qubit_number(physical_qubit)
        self._validate_logical_qubit_number(logical_qubit)
        self.z(self.__data[logical_qubit][physical_qubit])

    def set_up_ancilla(self, logical_qubit = 0):
        """Set up gates for ancilla based on entries in the parity matrix

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to set up ancilla gates for. Should be either 0 or 1 at present.

            Notes
            -----
            The ancilla needed are determined from the parity matrix.
        """
        self._validate_logical_qubit_number(logical_qubit)
        self.h(self.__mx[logical_qubit])
        self.h(self.__mz[logical_qubit])
        self.barrier()
        #apply CX gates according to the parity matrix
        for index in range (self.__num_ancilla):
            parity_row = self.__parity_check_matrix[index]
            for column_number in range(self.__num_data):
                if parity_row[column_number] ==1:             
                    self.cx(self.__mx[logical_qubit][index],self.__data[logical_qubit][column_number])  
        self.barrier()
        #apply CZ gates according to the parity matrix
        #done separately so Qiskit diagram is easier to review
        for index in range (self.__num_ancilla):
            parity_row = self.__parity_check_matrix[index]
            for column_number in range(self.__num_data):
                if parity_row[column_number] ==1:             
                    self.cz(self.__mz[logical_qubit][index],self.__data[logical_qubit][column_number])  
        self.barrier()
        #apply final hadamards to all ancillas
        for index in range (self.__num_ancilla):
            self.h(self.__mx[logical_qubit][index])
            self.h(self.__mz[logical_qubit][index])
        

    def logical_measure(self, logical_qubit = 0):
        """Makes gates to measure a logical qubit

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to measure. Should be either 0 or 1 at present.
        """
        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__num_ancilla):
            self.measure(self.__mx[logical_qubit][index], self.__mx_classical[logical_qubit][index])
            self.measure(self.__mz[logical_qubit][index], self.__mz_classical[logical_qubit][index])

        #if self.__correct_errors:
        if self.__extend_ancilla:
            for index in range(self.__num_extra_ancilla):
                self.measure(self.__extra_ancilla[logical_qubit][index], 
                            self.__extra_ancilla_classical[logical_qubit][index])

        for index in range(self.__num_data):
            self.measure(self.__data[logical_qubit][index], self.__data_classical[logical_qubit][index])

    def correct_errors(self, logical_qubit = 0, mct = False):
        """ Produces circuit to correct errors.  Note, need to swap ancilla bits to match how printed out.
            Reads through Parity matrix to determine the corrections to be applied.

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits on which to correct error. Should be either 0 or 1 at present.
            mct: bool
                Controls whether an MCT gate shall be used

            Notes
            -----
            The error correcting circuit is either set up with MCT gates, which is logically simpler but needs
            more gates, or without MCT gates, which is more difficult to program but needs less gates.
            In the latter case the complexity is to take into account corrections already applied when looking at
            two or three bit corrections.
            
            In both cases the error correcting gates are determined from the parity matrix.

        """

        if mct:
            if logical_qubit not in [0, 1]:
                raise ValueError("errors can only be corrected for one or two logical qubit at present")
        else:
            if logical_qubit !=0:
                raise ValueError("errors can only be corrected for one logical qubit at present if mct as not used ")
            if not self.__extend_ancilla: 
                raise ValueError("extra ancilla are needed to correct errors without mct")    
    
        transpose_parity = self._transpose_parity()

        qubit_data = {i: {"count":0} for i in range(self.__num_data)}
        single_CX_updates_list = []

        for qubit in qubit_data:
        # read the relevant column of the parity check matrix
            count = 0
            bit_list = transpose_parity[qubit]
            for bits in bit_list:
                if bits == 1:
                    count = count + 1
            qubit_data.update({qubit:{"count":count}})


        if mct:
            for qubit in range(self.__num_data):
                bit_list = transpose_parity[qubit]
                #x ancilla errors
                #flip zero ancilla bit to one
                for bit_index in range(self.__num_ancilla): 
                    if bit_list[bit_index] == 0:
                        self.x(self.__mz[logical_qubit][bit_index])
                # use MCT gate to bit flip incorrect qubit
                self.mct([self.__mz[logical_qubit][0], 
                              self.__mz[logical_qubit][1], 
                              self.__mz[logical_qubit][2]],
                              self.__data[logical_qubit][qubit])
                #flip zero ancilla bits back
                for bit_index in range(self.__num_ancilla): 
                    if bit_list[bit_index] == 0:
                        self.x(self.__mz[logical_qubit][bit_index])

                #z ancilla errors
                #flip zero ancilla bit to one
                for bit_index in range(self.__num_ancilla): 
                    if bit_list[bit_index] == 0:
                        self.x(self.__mx[logical_qubit][bit_index])
                # use MCT gate and Hadamard to bit flip incorrect qubit
                self.h(self.__data[logical_qubit][qubit])
                self.mct([self.__mx[logical_qubit][0], 
                              self.__mx[logical_qubit][1], 
                              self.__mx[logical_qubit][2]],
                              self.__data[logical_qubit][qubit])
                self.h(self.__data[logical_qubit][qubit])
                #flip zero ancilla bits back
                for bit_index in range(self.__num_ancilla): 
                    if bit_list[bit_index] == 0:
                        self.x(self.__mx[logical_qubit][bit_index])
                
        else:
            for qubit in range(self.__num_data):
                bit_list = transpose_parity[qubit]
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")      
                if count == 1:
                    for bit_index in range(self.__num_ancilla): 
                        if bit_list[bit_index] == 1:
                            self.cx(self.__mz[logical_qubit][bit_index], self.__data[logical_qubit][qubit])    
                            single_CX_updates_list.append([qubit, bit_index])
                            self.cz(self.__mx[logical_qubit][bit_index], self.__data[logical_qubit][qubit]) 
                            
            extra_ancilla = 0   
            for qubit in range(self.__num_data):
                bit_list = transpose_parity[qubit]
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")           
                if count == 2:      
                    for bit_index in range(self.__num_ancilla): 
                        first_bit = 0
                        second_bit = 0   
                        if count ==2:   # need a CCNOT gate
                            for bit_index in range(self.__num_ancilla): 
                                if bit_list[bit_index] == 1:
                                    if first_bit == 0:
                                        first_bit = bit_index
                                    else:
                                        second_bit = bit_index
                    self.ccx(self.__mz[logical_qubit][first_bit], 
                            self.__mz[logical_qubit][second_bit], 
                            self.__extra_ancilla[logical_qubit][extra_ancilla])
                    self.cx(self.__extra_ancilla[logical_qubit][extra_ancilla], 
                            self.__data[logical_qubit][qubit])
                    self.cz(self.__extra_ancilla[logical_qubit][extra_ancilla], 
                            self.__data[logical_qubit][qubit])

                    for items in single_CX_updates_list:
                        other_impacted_qubit = items[0]
                        bit_index = items[1]
                        if first_bit == bit_index or second_bit == bit_index:
                            self.cx(self.__extra_ancilla[logical_qubit][extra_ancilla], 
                                    self.__data[logical_qubit][other_impacted_qubit]) 
                            self.cz(self.__extra_ancilla[logical_qubit][extra_ancilla], 
                                    self.__data[logical_qubit][other_impacted_qubit]) 
                    extra_ancilla = extra_ancilla + 1

            for qubit in range(self.__num_data):
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")  
                if count == 3:
                    self.ccx(self.__extra_ancilla[logical_qubit][0], 
                            self.__extra_ancilla[logical_qubit][1], 
                            self.__extra_ancilla[logical_qubit][3]) 
                    self.ccx(self.__extra_ancilla[logical_qubit][0], 
                            self.__extra_ancilla[logical_qubit][2], 
                            self.__extra_ancilla[logical_qubit][3]) 
                    self.ccx(self.__extra_ancilla[logical_qubit][1], 
                            self.__extra_ancilla[logical_qubit][2], 
                            self.__extra_ancilla[logical_qubit][3]) 
                    #need to undo impact of all gates made earlier as odd parity by inspection of codes.
                    #maybe later could add code to check the changes made, and show they have odd parity.
                    for gate_needed in range(self.__num_data):
                        self.cx(self.__extra_ancilla[logical_qubit][3], 
                                self.__data[logical_qubit][gate_needed])
                        self.cz(self.__extra_ancilla[logical_qubit][3], 
                                self.__data[logical_qubit][gate_needed])

            #need to reverse CCX gates
            for qubit in range(self.__num_data):
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")  
                if count == 3:
                    self.ccx(self.__extra_ancilla[logical_qubit][0], 
                            self.__extra_ancilla[logical_qubit][1], 
                            self.__extra_ancilla[logical_qubit][3]) 
                    self.ccx(self.__extra_ancilla[logical_qubit][0], 
                            self.__extra_ancilla[logical_qubit][2], 
                            self.__extra_ancilla[logical_qubit][3]) 
                    self.ccx(self.__extra_ancilla[logical_qubit][1], 
                            self.__extra_ancilla[logical_qubit][2], 
                            self.__extra_ancilla[logical_qubit][3]) 

            extra_ancilla = 0   
            for qubit in range(self.__num_data):
                bit_list = transpose_parity[qubit]
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")           
                if count == 2:      
                    for bit_index in range(self.__num_ancilla): 
                        first_bit = 0
                        second_bit = 0   
                        if count ==2:   # need a CCNOT gate
                            for bit_index in range(self.__num_ancilla): 
                                if bit_list[bit_index] == 1:
                                    if first_bit == 0:
                                        first_bit = bit_index
                                    else:
                                        second_bit = bit_index
                ## need to add a ccx gate
                    self.ccx(self.__mz[logical_qubit][first_bit], 
                            self.__mz[logical_qubit][second_bit], 
                            self.__extra_ancilla[logical_qubit][extra_ancilla])
                    extra_ancilla = extra_ancilla + 1

    def decode(self, logical_qubit = 0):
        """Uncomputer setting up logical zero for data qubit.  This is a reversal of the encoding circuit.

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to set up logical zero for. Should be either 0 or 1 at present.

            Notes
            -----
            The gates needed are determined from the parity matrix.
        """
        self._validate_logical_qubit_number(logical_qubit)
        parity_matrix_totals = [ 0 for x in range(self.__num_data)] # define an empty list ready to work out parity_matrix_totals
        for parity_row in self.__parity_check_matrix:
            for index in range(self.__num_data):
                parity_matrix_totals[index] = parity_matrix_totals[index] + parity_row[index]

        for index in range (self.__num_data):
            if parity_matrix_totals[index] == 1:
                for parity_row in self.__parity_check_matrix:
                    if parity_row[index] == 1:              #correct row to build ancilla from
                        for column_number in range(self.__num_data):
                            if column_number != index:
                                if parity_row[column_number] == 1:
                                        self.cx(self.__data[logical_qubit][index], self.__data[logical_qubit][column_number])

        for index in range (self.__num_data):
            if parity_matrix_totals[index] == 1:
                self.h(self.__data[logical_qubit][index])

    def logical_gate_X(self, logical_qubit = 0):
        """Apply a logical X gate

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to apply logical X gate to. Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit = 0)
        for index in range(self.__num_data):
            self.x(self.__data[logical_qubit][index])

    def logical_gate_H(self, logical_qubit = 0):
        """Apply a logical H gate

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to apply Hadamard on. Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__num_data):
            self.h(self.__data[logical_qubit][index])

    def logical_gate_Z(self, logical_qubit = 0):
        """Apply a logical Z gate

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to apply logical Z gate on. Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__num_data):
            self.z(self.__data[logical_qubit][index])
    
    def logical_gate_CX(self, logical_control_qubit, logical_target_qubit):
        """Apply a logical CX gate
            
            Parameters
            ----------

                logical_control_qubit : int
                    Number of the logical "data" qubit which controls the CX gate
                logical_target_qubit : int
                    Number of the logical "data" qubit which is the target for the CX gate
        """
        self._validate_logical_qubit_number(logical_control_qubit)
        self._validate_logical_qubit_number(logical_target_qubit)
        if logical_control_qubit == logical_target_qubit:   
            raise ValueError("the control and target qubits for the logical CX must be different")
        for index in range(self.__num_data):
            self.cx(self.__data[logical_control_qubit][index], 
                    self.__data[logical_target_qubit][index])
    
    def dummy_decoding(self, input_string, logical_qubit = 0):
        """Instead of the full decoding circuit a dummy circuit is set up for testing.
        
        Parameters
        ----------

            input_string : str
                String to control gates set up
            logical_qubit: int
                Number of the logical "data" qubits to apply logical Z gate on. Should be either 0 or 1 at present.

        Notes
        -----
        This function is not currently used by any workbook but is retained in case it is useful in future.
        """
        if len(input_string) != (self.__num_data):
            raise Exception('When creating a dummy decoding circuit the string given must be length {self.__num_data}')
        index = len(input_string) - 1
        #need to count down as naming convention of gates is opposite.
        for bit in input_string:
            if bit == '1':
                self.x(self.__data[logical_qubit][index])
            index = index - 1
    
        return

    
    def _transpose_parity(self):
        """Transposes the parity check matrix"""
        column = []
        parity_check_transpose = []
        for row_count in range(self.__num_data):
            for column_count in range(self.__num_ancilla):
                item = self.__parity_check_matrix[column_count][row_count] 
                column.append(item)
            parity_check_transpose.append(column)
            column = []
        return(parity_check_transpose)

    def _validate_logical_qubit_number(self, logical_qubit):
        """Validates the logical qubit number.  Code might be enhanced in the future.

            Parameters:
            -----------

            logical_qubit : int
                Number of the logical "data" qubit to check
        """
        if logical_qubit not in [0, 1]:
            raise ValueError("The qubit to be processed must be indexed as 0 or 1 at present")

    def _validate_physical_qubit_number(self, physical_qubit):
        """ Validate the physical qubit number 

            Parameters
            ----------
            physical qubit : int
                Number of the physical qubit to validate
        """        

        if physical_qubit > self.__num_data - 1 :
            raise ValueError("Qubit index must be in range of data qubits")
        if physical_qubit < 0:
            raise ValueError("Qubit index must be in range of data qubits")


class BaconShorCodeLogicalQubit(QuantumCircuit):
    """Generates the gates for one logical Qubits of the Bacon Shor code

        Parameters
        ----------
        d : int
            Number of logical "data" qubits to be initialised. Should be either 1 or 2 at present.
            Only the case with 1 qubit has been fully tested.
        data_qubits : int
            Number of data qubits.  Usually nine.
        ancilla_qubits : int
            Number of ancilla qubits.  Usually two.
        ancilla : int
            Number of ancilla.  Usually two for X and Z.
        blocks : int
            Number of blocks 
        logical_z : bool
            True if a logical z is set up.  Otherwise false
        """

    def __init__(self, d, data_qubits, ancilla_qubits, ancillas, blocks, logical_one, logical_z):
        """Initialise qubit"""
        if d > 2:
            raise ValueError("Qiskit can only handle 32 quits.  So can't set up more than two logical qubits.")
        self.__data_qubits = data_qubits
        self.__ancilla_qubits = ancilla_qubits
        self.__ancillas = ancillas
        self.__blocks = blocks
        self.__logical_one = logical_one
        self.__logical_z = logical_z
        self.define_data()
        list_of_all_registers = self.define_registers(d)
        # extend quantum circuits
        super().__init__(*list_of_all_registers)


    def define_data(self):
        """Define standing data"""
        self.__data = []
        self.__ancilla = []
        self.__data_classical = []
        self.__ancilla_classical = []

    def define_registers(self, d):
        """Set up registers used based on number of logical qubits and whether error checking is needed.

        Parameters
        ----------
        d : int
            Number of the logical "data" qubits to be initialised. Should be either 0 or 1 at present.
        
        Notes
        -----
        The registers are stored in a list so that they can be indexed to simplify subsequent code.

        """
        list_of_all_registers = []
        for index in range(d):
            self.__qubit_no = str(index)
            # Quantum registers
            self.__data.append(QuantumRegister(self.__data_qubits, "data " + self.__qubit_no))
            self.__ancilla.append(QuantumRegister(self.__ancilla_qubits, "ancilla "+ self.__qubit_no))
            list_of_all_registers.append(self.__data[index])
            list_of_all_registers.append(self.__ancilla[index])

            # Classical registers
            self.__data_classical.append(ClassicalRegister(self.__data_qubits, "measure_data " + self.__qubit_no))
            self.__ancilla_classical.append(ClassicalRegister(self.__ancilla_qubits, "measure_ancilla "+ self.__qubit_no) )
            list_of_all_registers.append(self.__data_classical[index])
            list_of_all_registers.append(self.__ancilla_classical[index]) 
        return (list_of_all_registers)

    def encoding_nft(self, logical_qubit = 0,):
        """ Adds an encoding non fault tolerant gate.  
        
        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to encode. Should be either 0 or 1 at present.
        logical_one: Bool
            If true set up the logical one.  Otherwise set up the logical zero.
        """
        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__data_qubits):
                self.reset(self.__data[logical_qubit][index])
        #Set to logical one if required
        if self.__logical_one:
            self.x(self.__data[logical_qubit][0])
        self.cx(self.__data[logical_qubit][0],self.__data[logical_qubit][self.__blocks])
        self.cx(self.__data[logical_qubit][0],self.__data[logical_qubit][self.__blocks * 2])
        self.barrier()
        return

    def encoding_ft(self, logical_qubit = 0):
        """ Adds an encoding non fault tolerant gate.  
        
        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to encode. Should be either 0 or 1 at present.
        """
        self._validate_logical_qubit_number(logical_qubit)
        for count in range(self.__blocks):
            first_qubit = count * self.__blocks
            second_qubit = count * self.__blocks + 1
            third_qubit = count * self.__blocks + 2
            self.h(self.__data[logical_qubit][first_qubit])
            self.cx(self.__data[logical_qubit][first_qubit],self.__data[logical_qubit][second_qubit])
            self.cx(self.__data[logical_qubit][first_qubit],self.__data[logical_qubit][third_qubit])
            if self.__logical_z:
                #only need post encoding Hadamard for the z_logical gate
                self.h(self.__data[logical_qubit][first_qubit])
                self.h(self.__data[logical_qubit][second_qubit])
                self.h(self.__data[logical_qubit][third_qubit])        
        self.barrier()
        return

    def x_testing(self, logical_qubit = 0, test_x_qubit = 0):
        """Introduces one X error

        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to test. Should be either 0 or 1 at present.
        
        test_x_qubit : int
            Qubit on which X error is introduced
        """

        self._validate_logical_qubit_number(logical_qubit)
        self._validate_physical_qubit_number(test_x_qubit)
        self.x(self.__data[logical_qubit][test_x_qubit])
        self.barrier()
        return

    def z_testing(self, logical_qubit = 0, test_z_qubit = 0):
        """Introduces one Z error

        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to test. Should be either 0 or 1 at present.
        test_z_qubit : int
            Qubit on which Z error is introduced
        """

        self._validate_logical_qubit_number(logical_qubit)
        self._validate_physical_qubit_number(test_z_qubit)
        self.z(self.__data[logical_qubit][test_z_qubit])
        self.barrier()
        return

    def x_stabilizers(self, logical_qubit = 0):
        """Function to set up x stabilizers or ancilla

        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to set up ancilla for. Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit)
        for ancilla in range ( 0 , self.__ancillas):
            # loop over ancillas
            self.h(self.__ancilla[0][ancilla + self.__ancillas])
            #ancilla count starts at ANCILLAS
            for count in range(self.__blocks):
                first_qubit = count * self.__blocks + ancilla
                second_qubit = count * self.__blocks + ancilla + 1
                self.cx(self.__ancilla[logical_qubit][ancilla + self.__ancillas], 
                        self.__data[logical_qubit][first_qubit])
                self.cx(self.__ancilla[logical_qubit][ancilla + self.__ancillas], 
                        self.__data[logical_qubit][second_qubit])
                #ancilla count starts at ANCILLAS
            self.h(self.__ancilla[0][ancilla + self.__ancillas])
        self.barrier()
        return

    def z_stabilizers(self, logical_qubit = 0):
        """Function to set up z stabilizers or ancilla

        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to set up ancilla for. Should be either 0 or 1 at present.
        """

        for ancilla in range (0 , self.__ancillas):
            for count in range(self.__blocks):
                first_qubit = count + self.__blocks * ancilla 
                second_qubit = count + self.__blocks * (ancilla + 1)
                self.cx(self.__data[logical_qubit][first_qubit], 
                        self.__ancilla[logical_qubit][ancilla])
                self.cx(self.__data[logical_qubit][second_qubit], 
                        self.__ancilla[logical_qubit][ancilla])
        self.barrier()
        return

    def logical_measure(self, logical_qubit = 0):
        """Function to measure a logical qubit
        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to measure. Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__data_qubits):
            self.measure(self.__data[logical_qubit][index], self.__data_classical[logical_qubit][index])
        for index in range(self.__ancilla_qubits):
            self.measure(self.__ancilla[logical_qubit][index], self.__ancilla_classical[logical_qubit][index])

    def _validate_logical_qubit_number(self, logical_qubit):
        """Validates the logical qubit number.  Code might be enhanced in the future.

        Parameters:
        -----------
        logical_qubit : int
            Number of the logical "data" qubit to check
        """

        if logical_qubit not in [0, 1]:
            raise ValueError("The qubit to be processed must be indexed as 0 or 1 at present")

    def _validate_physical_qubit_number(self, physical_qubit):
        """ Validate the physical qubit number 

            Parameters
            ----------
            physical qubit : int
                Number of the physical qubit to validate
        """        

        if physical_qubit > self.__data_qubits - 1 :
            raise ValueError("Qubit index must be in range of data qubits")
        if physical_qubit < 0:
            raise ValueError("Qubit index must be in range of data qubits")
