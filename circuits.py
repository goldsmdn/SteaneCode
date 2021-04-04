"""Class to handle logical qubits for the Steane code"""

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute, Aer

class SteaneCodeLogicalQubit(QuantumCircuit):
    """Generates the gates for one or two logical Qubits of the Steane code

        Parameters
        ----------
        d : int
            Number of logical "data" qubits to be initialised. Should be either 1 or 2 at present.
        parity_check_matrix : list
            Holds the parity check matrix from which the gates will be constructed.
        correct_errors : bool 
            True if need to make a circuit to correct errors. 
    
        Notes
        -----
        Uses super to inherit methods from parent.
        """

    def __init__(self, d, parity_check_matrix, correct_errors,*args, **kwargs):
        """Initialise qubit"""
        self.__correct_errors = correct_errors
        if self.__correct_errors:
            if d > 1:
                raise ValueError("Can't correct errors with two logical qubits due to memory size restrictions")
        self.__parity_check_matrix = parity_check_matrix
        # define valid codewords to check they are orthogonal to the parity check matrix.
        self.__codewords = [[0,0,0,0,0,0,0],   
                            [1,0,1,0,1,0,1],
                            [0,1,1,0,0,1,1],
                            [1,1,0,0,1,1,0],
                            [0,0,0,1,1,1,1],
                            [1,0,1,1,0,1,0],
                            [0,1,1,1,1,0,0],
                            [1,1,0,1,0,0,1]]
        
        self.__num_data = 7             #seven data qubits for the Steane code
        self.__num_ancilla = 3          #six ancilla qubits, three x and three z
        self.__num_extra_ancilla = 4    #four extra ancilla for decoding

        self.__data = []
        self.__mx = []
        self.__mz = []
        self.__extra_ancilla = []
        self.__data_classical = []
        self.__mx_classical = []
        self.__mz_classical = []
        self.__extra_ancilla_classical = []
        list_of_all_registers = []
        #self.__qubit_no = str(0)
        
        for index in range (d):
            
            self.__qubit_no = str(index)
            # Quantum registers
            self.__data.append(QuantumRegister(self.__num_data, "data " + self.__qubit_no))
            self.__mx.append(QuantumRegister(self.__num_ancilla, "ancilla_X " + self.__qubit_no))
            self.__mz.append(QuantumRegister(self.__num_ancilla, "ancilla_Z " + self.__qubit_no))
            list_of_all_registers.append(self.__data[index])
            list_of_all_registers.append(self.__mx[index])
            list_of_all_registers.append(self.__mz[index])

            if self.__correct_errors:
                self.__extra_ancilla.append(QuantumRegister(self.__num_extra_ancilla, name="extra_ancilla" + self.__qubit_no)) 
                list_of_all_registers.append(self.__extra_ancilla[index])
            # Classical registers
            self.__data_classical.append(ClassicalRegister(self.__num_data, "measure_data " + self.__qubit_no))
            self.__mx_classical.append(ClassicalRegister(self.__num_ancilla, "measure_ancilla_X " + self.__qubit_no))
            self.__mz_classical.append(ClassicalRegister(self.__num_ancilla, "measure_ancilla_Z " + self.__qubit_no))
            list_of_all_registers.append(self.__data_classical[index])
            list_of_all_registers.append(self.__mx_classical[index]) 
            list_of_all_registers.append(self.__mz_classical[index])
            if self.__correct_errors:
                self.__extra_ancilla_classical.append(
                    ClassicalRegister(self.__num_extra_ancilla, "measure_extra_ancilla " + self.__qubit_no))
                list_of_all_registers.append(self.__extra_ancilla_classical[index]) 
        
        super().__init__(*list_of_all_registers)

        #    list_of_all_registers = [self.__data[0], self.__mx[0], self.__mz[0], self.__extra_ancilla[0],
        #                    self.__data_classical[0], self.__mx_classical[0], self.__mz_classical[0], self.__extra_ancilla_classical[0]]

        
        #self.__data_0 = QuantumRegister(self.__num_data, "data " + self.__qubit_no)
        #self.__mx_0 = QuantumRegister(self.__num_ancilla, "ancilla_X " + self.__qubit_no)
        #self.__mz_0 = QuantumRegister(self.__num_ancilla, "ancilla_Z " + self.__qubit_no)
        

        # Spare ancillas (e.g. for readout)
        #if self.__correct_errors:
        #    self.__extra_ancilla_0 = QuantumRegister(self.__num_extra_ancilla, name="extra_ancilla" + self.__qubit_no)

        #classical registers
        #self.__data_classical_0 = ClassicalRegister(self.__num_data, "measure_data " + self.__qubit_no)
        #self.__mx_classical_0 = ClassicalRegister(self.__num_ancilla, "measure_ancilla_X " + self.__qubit_no)
        #self.__mz_classical_0 = ClassicalRegister(self.__num_ancilla, "measure_ancilla_Z " + self.__qubit_no)
        #if self.__correct_errors:
        #    self.__extra_ancilla_classical_0 = ClassicalRegister(self.__num_extra_ancilla, "measure_extra_ancilla " + self.__qubit_no)

        #if d == 2:
        #    self.__qubit_no = str(d-1)
        #    self.__data_1 = QuantumRegister(self.__num_data, "data " + self.__qubit_no)
        #    self.__mx_1 = QuantumRegister(self.__num_ancilla, "ancilla_X " + self.__qubit_no)
        #    self.__mz_1 = QuantumRegister(self.__num_ancilla, "ancilla_Z " + self.__qubit_no)

            # Spare ancillas (e.g. for readout)
            #self.__extra_ancilla_1 = QuantumRegister(self.__num_extra_ancilla, name="extra_ancilla" + self.__qubit_no)

            #classical registers
        #    self.__data_classical_1 = ClassicalRegister(self.__num_data, "measure_data " + self.__qubit_no)
        #    self.__mx_classical_1 = ClassicalRegister(self.__num_ancilla, "measure_ancilla_X " + self.__qubit_no)
        #    self.__mz_classical_1 = ClassicalRegister(self.__num_ancilla, "measure_ancilla_Z " + self.__qubit_no)

        # user super to inherit all methods from Quantum circuits
        #if d == 1:
        #        if self.__correct_errors:
        #            list_of_all_registers = [self.__data[0], self.__mx[0], self.__mz[0], self.__extra_ancilla[0],
        #                    self.__data_classical[0], self.__mx_classical[0], self.__mz_classical[0], self.__extra_ancilla_classical[0]]
        #            print("list_of_all_registers", list_of_all_registers)
        #            super().__init__(*list_of_all_registers)
        #        else:
        #            # don't need extra ancilla if don't correct errors.
        #            super().__init__(self.__data[0], self.__mx[0], self.__mz[0],
        #                self.__data_classical[0], self.__mx_classical[0], self.__mz_classical[0])

        #elif d == 2:
        #    super().__init__(
        #            self.__data[0], self.__mx[0], self.__mz[0],
        ##            self.__data_classical[0], self.__mx_classical[0], self.__mz_classical[0],
         #           self.__data[1], self.__mx[1], self.__mz[1],
         #           self.__data_classical[1], self.__mx_classical[1], self.__mz_classical[1])

                # user super to inherit all methods from Quantum circuits
        #if d == 1:
        #        if self.__correct_errors:
        #            super().__init__(self.__data, self.__mx_0, self.__mz_0, self.__extra_ancilla_0,
        #                    self.__data_classical_0, self.__mx_classical_0, self.__mz_classical_0, self.__extra_ancilla_classical_0)
        #        else:
        #            # don't need extra ancilla if don't correct errors.
        #            super().__init__(self.__data_0, self.__mx_0, self.__mz_0,
        #                self.__data_classical_0, self.__mx_classical_0, self.__mz_classical_0)

        #elif d == 2:
        #    super().__init__(
        #            self.__data_0, self.__mx_0, self.__mz_0,
        #            self.__data_classical_0, self.__mx_classical_0, self.__mz_classical_0,
        #            self.__data_1, self.__mx_1, self.__mz_1,
        #            self.__data_classical_1, self.__mx_classical_1, self.__mz_classical_1)
        
        #else:
        #    raise ValueError('Please enter 1 or 2 when initialising the qubits.  Currently only up to two qubits are supported')

        self.validate_parity_matrix()

    #def update_registers(self)


    def validate_parity_matrix(self):
        """validate the parity matrix against the allowed codewords"""
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

    def set_up_logical_zero(self, logical_qubit):
        """Set up logical zero for data qubit

        Parameters
        ----------
        logical_qubit : int
            Number of the logical "data" qubits to be initialised. Should be either 0 or 1 at present.

        """
        self._validate_logical_qubit_number(logical_qubit)
        
        parity_matrix_totals = [ 0 for x in range(self.__num_data)] # define an empty list ready to work out parity_matrix_totals

        for parity_row in self.__parity_check_matrix:
            for index in range(self.__num_data):
                parity_matrix_totals[index] = parity_matrix_totals[index] + parity_row[index]

        count = 0
        for index in range (self.__num_data):
            if parity_matrix_totals[index] == 1:
                count = count + 1
                #if logical_qubit == 0:
                #    self.h(self.__data_0[index])
                #elif logical_qubit == 1:
                #    self.h(self.__data_1[index])
                #else:
                #    raise ValueError("not able to set up logical zero")
                self.h(self.__data[logical_qubit][index])
                for parity_row in self.__parity_check_matrix:
                    if parity_row[index] == 1:              #correct row to build ancilla from
                        for column_number in range(self.__num_data):
                            if column_number != index:
                                if parity_row[column_number] == 1:
                                    self.cx(self.__data[logical_qubit][index],self.__data[logical_qubit][column_number])
                                #    if logical_qubit == 0:
                                #        self.cx(self.__data_0[index],self.__data_0[column_number])
                                #    elif logical_qubit == 1:
                                #        self.cx(self.__data_1[index],self.__data_1[column_number])
                                #    else:
                                #        raise ValueError("not able to set up logical zero")

        if count != self.__num_ancilla:
            raise ValueError('Unable to construct matrix as parity matrix does not match the ancilla needed')   

    def force_X_error(self,qubit,logical_qubit):
        """ Force an X error on one physical qubit

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to force error on. Should be either 0 or 1 at present.
            qubit : int
                Number of qubit to force error on.

        """
        self._validate_logical_qubit_number(logical_qubit)
        if qubit > self.__num_data - 1 :
            raise ValueError("Qubit index must be in range of data qubits")
        if qubit < 0:
            raise ValueError("Qubit index must be in range of data qubits")

        self.x(self.__data[logical_qubit][qubit])

        #if logical_qubit == 0:
        #    self.x(self.__data_0[qubit])
        #elif logical_qubit == 1:
        #    self.x(self.__data_1[qubit])
        #else:
        #    raise ValueError("Unable to force an X error on the logical qubit")
        

    def force_Z_error(self,qubit,logical_qubit):
        """ Force Z error on one physical qubit

            Parameters
            ---------- 
            logical_qubit: int
                Number of the logical "data" qubits to force error on. Should be either 0 or 1 at present.
            qubit : int
                Number of qubit to force error on.

        """
        self._validate_logical_qubit_number(logical_qubit)
        if qubit > self.__num_data - 1 :
            raise ValueError("Qubit index must be in range of data qubits")
        if qubit < 0:
            raise ValueError("Qubit index must be in range of data qubits")
        self.z(self.__data[logical_qubit][qubit])
        #if logical_qubit == 0:
        #    self.z(self.__data_0[qubit])
        #elif logical_qubit == 1:
        #    self.z(self.__data_1[qubit])
        #else:
        #    raise ValueError("Unable to force an Z error on the logical qubit")

    def set_up_ancilla(self,logical_qubit):
        """set up gates for ancilla based on entries in the parity matrix

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to set up ancilla gates for. Should be either 0 or 1 at present.

        """
        self._validate_logical_qubit_number(logical_qubit)
        #apply hadamards to all ancillas
        #for index in range (self.__num_ancilla):
        #    if logical_qubit == 0:
        #        self.h(self.__mx_0[index])
        #        self.h(self.__mz_0[index])
        #    elif logical_qubit == 1:
        #        self.h(self.__mx_1[index])
        #        self.h(self.__mz_1[index])
        #   else:
        #        raise ValueError("Unable to set up ancillas")
        self.h(self.__mx[logical_qubit])
        self.h(self.__mz[logical_qubit])
        #apply CX gates according to the parity index
        for index in range (self.__num_ancilla):
            parity_row = self.__parity_check_matrix[index]
            for column_number in range(self.__num_data):
                if parity_row[column_number] ==1:
                #    if logical_qubit == 0:
                #        self.cx(self.__mx_0[index],self.__data_0[column_number])
                #        self.cz(self.__mz_0[index],self.__data_0[column_number]) 
                #    elif logical_qubit == 1:
                #        self.cx(self.__mx_1[index],self.__data_1[column_number])
                #        self.cz(self.__mz_1[index],self.__data_1[column_number])    
                #    else:
                #        raise ValueError("Unable to set up ancillas")      
                    self.cx(self.__mx[logical_qubit][index],self.__data[logical_qubit][column_number])             
                    self.cz(self.__mz[logical_qubit][index],self.__data[logical_qubit][column_number])  
        #apply final hadamards to all ancillas
        for index in range (self.__num_ancilla):
            #if logical_qubit == 0:
            #    self.h(self.__mx_0[index])
            #    self.h(self.__mz_0[index])
            #elif logical_qubit == 1:
            #    self.h(self.__mx_1[index])
            #    self.h(self.__mz_1[index])
            #else:
            #    raise ValueError("Unable to set up ancillas")
            self.h(self.__mx[logical_qubit][index])
            self.h(self.__mz[logical_qubit][index])

    def logical_measure(self,logical_qubit):
        """Makes gates to measure a logical qubit

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to measure. Should be either 0 or 1 at present.

        """
        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__num_ancilla):
            # need to swap measurement qubits so that the measurements match the normal format of the codewords
            #if logical_qubit == 0:
            #    self.measure(self.__mx_0[index], self.__mx_classical_0[self.__num_ancilla - index-1])
            #    self.measure(self.__mz_0[index], self.__mz_classical_0[self.__num_ancilla - index-1])
            #elif logical_qubit == 1:
            #    self.measure(self.__mx_1[index], self.__mx_classical_1[self.__num_ancilla - index-1])
            #    self.measure(self.__mz_1[index], self.__mz_classical_1[self.__num_ancilla - index-1])
            #else:
            #    raise ValueError("Unable to meaure qubits")
            self.measure(self.__mx[logical_qubit][index], self.__mx_classical[logical_qubit][self.__num_ancilla - index-1])
            self.measure(self.__mz[logical_qubit][index], self.__mz_classical[logical_qubit][self.__num_ancilla - index-1])

        if self.__correct_errors:
            for index in range(self.__num_extra_ancilla):
                #if logical_qubit == 0:
                #    self.measure(self.__extra_ancilla_0[index], self.__extra_ancilla_classical_0[self.__num_extra_ancilla - index- 1])
                #elif logical_qubit == 1:
                    # should not be called at present - for future expansion
                    #self.measure(self.__extra_ancilla_1[index],self.__extra_ancilla_classical_1[self.__num_extra_ancilla - index- 1])
                #else:
                #    raise ValueError("Unable to meaure qubits")
                self.measure(self.__extra_ancilla[logical_qubit][index], 
                            self.__extra_ancilla_classical[logical_qubit][self.__num_extra_ancilla - index- 1])

        for index in range(self.__num_data):
            # need to swap measurement qubits so that the measurements match the normal format of the codewords
            #if logical_qubit == 0:
            #    self.measure(self.__data_0[index], self.__data_classical_0[self.__num_data - index-1])
            #elif logical_qubit == 1:
            #    self.measure(self.__data_1[index], self.__data_classical_1[self.__num_data - index-1])
            #else:
            #    raise ValueError("Unable to meaure qubits")
            self.measure(self.__data[logical_qubit][index], self.__data_classical[logical_qubit][self.__num_data - index-1])

    def correct_errors(self,logical_qubit):
        """ produces circuit to correct  errors.  Note, need to swap ancilla bits to match how printed out.

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits on which to correct error. Should be either 0 or 1 at present.

        """
        if logical_qubit !=0:
            raise ValueError("errors can only be corrected for one logical qubit at present")
        else:
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

            for qubit in range(self.__num_data):
                bit_list = transpose_parity[qubit]
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")
                if count == 1:
                    for bit_index in range(self.__num_ancilla): 
                        if bit_list[bit_index] == 1:
                            #self.cx(self.__mz_0[bit_index], self.__data_0[qubit])
                            self.cx(self.__mz[logical_qubit][bit_index], self.__data[logical_qubit][qubit])    
                            single_CX_updates_list.append([qubit, bit_index])
                            self.cz(self.__mx[logical_qubit][bit_index], self.__data[logical_qubit][qubit])                     
                            #self.cz(self.__mx_0[bit_index], self.__data_0[qubit])

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
                    #self.ccx(self.__mz_0[first_bit], self.__mz_0[second_bit], self.__extra_ancilla_0[extra_ancilla])
                    #self.cx(self.__extra_ancilla_0[extra_ancilla], self.__data_0[qubit])
                    #self.cz(self.__extra_ancilla_0[extra_ancilla], self.__data_0[qubit])
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
                            # need a CX / CZ gate to reverse out changes from count 1 gates, or these will show the wrong answer.
                            #self.cx(self.__extra_ancilla_0[extra_ancilla], self.__data_0[other_impacted_qubit]) 
                            #self.cz(self.__extra_ancilla_0[extra_ancilla], self.__data_0[other_impacted_qubit]) 
                            self.cx(self.__extra_ancilla[logical_qubit][extra_ancilla], 
                                    self.__data[logical_qubit][other_impacted_qubit]) 
                            self.cz(self.__extra_ancilla[logical_qubit][extra_ancilla], 
                                    self.__data[logical_qubit][other_impacted_qubit]) 
                    extra_ancilla = extra_ancilla + 1

            for qubit in range(self.__num_data):
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")  
                if count == 3:
                    #self.ccx(self.__extra_ancilla_0[0], self.__extra_ancilla_0[1], self.__extra_ancilla_0[3]) 
                    #self.ccx(self.__extra_ancilla_0[0], self.__extra_ancilla_0[2], self.__extra_ancilla_0[3]) 
                    #self.ccx(self.__extra_ancilla_0[1], self.__extra_ancilla_0[2], self.__extra_ancilla_0[3]) 
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
                        #self.cx(self.__extra_ancilla_0[3], self.__data_0[gate_needed])
                        #self.cz(self.__extra_ancilla_0[3], self.__data_0[gate_needed])
                        self.cx(self.__extra_ancilla[logical_qubit][3], 
                                self.__data[logical_qubit][gate_needed])
                        self.cz(self.__extra_ancilla[logical_qubit][3], 
                                self.__data[logical_qubit][gate_needed])

            #need to reverse CCX gates
            for qubit in range(self.__num_data):
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")  
                if count == 3:
                    #self.ccx(self.__extra_ancilla_0[0], self.__extra_ancilla_0[1], self.__extra_ancilla_0[3]) 
                    #self.ccx(self.__extra_ancilla_0[0], self.__extra_ancilla_0[2], self.__extra_ancilla_0[3]) 
                    #self.ccx(self.__extra_ancilla_0[1], self.__extra_ancilla_0[2], self.__extra_ancilla_0[3]) 
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
                    #self.ccx(self.__mz_0[first_bit], self.__mz_0[second_bit], self.__extra_ancilla_0[extra_ancilla])
                    self.ccx(self.__mz[logical_qubit][first_bit], 
                             self.__mz[logical_qubit][second_bit], 
                             self.__extra_ancilla[logical_qubit][extra_ancilla])
                    extra_ancilla = extra_ancilla + 1

    def decode(self, logical_qubit):
        """Uncomputer setting up logical zero for data qubit.  This is the encoding circuit reversed.

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to set up logical zero for. Should be either 0 or 1 at present.

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
                                        #if logical_qubit == 0:
                                        #    self.cx(self.__data_0[index], self.__data_0[column_number])
                                        #elif logical_qubit == 1:
                                        #    self.cx(self.__data_1[index], self.__data_1[column_number])
                                        #else:
                                        #    raise ValueError("Unable to decode logical qubit")
                                        self.cx(self.__data[logical_qubit][index], self.__data[logical_qubit][column_number])

        for index in range (self.__num_data):
            if parity_matrix_totals[index] == 1:
                #if logical_qubit == 0:
                #    self.h(self.__data_0[index])
                #elif logical_qubit == 1:
                #    self.h(self.__data_1[index])
                #else:
                #    raise ValueError("Unable to decode logical qubit")
                self.h(self.__data[logical_qubit][index])

    def logical_gate_X(self, logical_qubit):
        """Apply a logical X gate

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to apply logical X gate to. Should be either 0 or 1 at present.

        """

        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__num_data):
            #if logical_qubit == 0:
            #    self.x(self.__data_0[index])
            #elif logical_qubit == 1:
            #    self.x(self.__data_1[index])
            #else:
            #    raise ValueError("Unable to apply X gate")
            self.x(self.__data[logical_qubit][index])

    def logical_gate_H(self, logical_qubit):
        """Apply a logical H gate

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to apply Hadamard on. Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__num_data):
            #if logical_qubit == 0:
            #    self.h(self.__data_0[index])
            #elif logical_qubit == 1:
            #    self.h(self.__data_1[index])
            #else:
            #    raise ValueError("Unable to apply X gate")
            self.h(self.__data[logical_qubit][index])

    def logical_gate_Z(self, logical_qubit):
        """Apply a logical Z gate

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to apply logical Z gate on. Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__num_data):
            #if logical_qubit == 0:
            #    self.z(self.__data_0[index])
            #elif logical_qubit == 1:
            #    self.z(self.__data_1[index])
            #else:
            #    raise ValueError("Unable to apply Z gate")
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
            #if logical_control_qubit == 0:
            #    self.cx(self.__data_0[index], self.__data_1[index])
            #elif logical_control_qubit == 1:
            #    self.cx(self.__data_1[index], self.__data_0[index])
            #else:
            #    raise ValueError("Unable to apply CX gate")
            self.cx(self.__data[logical_control_qubit][index], 
                    self.__data[logical_target_qubit][index])
    
    def _transpose_parity(self):
        """transposes the parity check matrix"""
        column = []
        parity_check_transpose = []
        for row_count in range(self.__num_data):
            for column_count in range(self.__num_ancilla):
                item = self.__parity_check_matrix[column_count][row_count] 
                column.append(item)
            parity_check_transpose.append(column)
            column = []
        return(parity_check_transpose)

    def _validate_logical_qubit_number(self, q):
        """Validates the logical qubit number.  Code might be enhanced in the future.

            Parameters:
            -----------

            q : int
                Number of the logical "data" qubit to check
        """
        if q not in [0, 1]:
            raise ValueError("The qubit to be processed must be indexed as 0 or 1 at present")

