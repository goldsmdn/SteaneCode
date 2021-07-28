"""Class to handle logical qubits for the Steane and Bacon Shor code"""

from typing import List
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from helper_functions import validate_integer

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
        ancilla : bool 
            True if need to set up ancilla.  For some circuits these are not needed.
        extend_ancilla : bool 
            True if need to add extra ancilla for error correction without using MCT gates
        fault_tolerant_b : bool
            True if need to set up scheme c for fault tolerant encoding with three rounds of measurement
            on the second logical qubit.
        fault_tolerant_c : bool
            True if need to set up an extra qubit for fault tolerance
        fault_tolerant_ancilla : bool   
            True if need to set up fault tolerant ancilla
        ancilla_rounds : int
            Number of rounds of ancilla measurement for fault tolerant ancilla
        data_round : int
            Number of rounds of ancilla measurement for fault tolerant encoding
        Notes
        -----
        Uses super to inherit methods from parent.  The code is derived from the parity matrix.
        The parity matrix is validated to ensure each row is orthogonal to each valid codeword.
        The number of data qubits is calculated the length of rows parity matrix.  
        The number of ancilla is calculated from the number of columns in the parity matrix.
        Ancilla qubits are only set up if these are needed.
        For error correction without MCT gates these ancilla are extended.
        An extra qubit can be added for a fault tolerant logical zero.
        Extra measurement ancilla are set up if there is more than one ancilla measurement round.
        """

    def __init__(self, d, parity_check_matrix, codewords, ancilla = True, extend_ancilla = False, 
                fault_tolerant_b = False, fault_tolerant_c = False,
                fault_tolerant_ancilla = False, ancilla_rounds = 1, data_rounds = 1):

        """Initialise qubit"""
        validate_integer(d)
        if d > 1:
            if extend_ancilla:
                raise ValueError("Can't set up extra ancilla with two logical qubits due to memory size restrictions")
            if fault_tolerant_ancilla:
                raise ValueError("Can't set up fault tolerant ancilla with two logical qubits due to memory size restrictions")
        if not ancilla:
            if fault_tolerant_ancilla:
                raise ValueError("Need to select ancillas to set up fault tolerant ancilla")
            if extend_ancilla:
                raise ValueError("Need to select ancillas to extend ancilla")
        if not fault_tolerant_ancilla:
            if ancilla_rounds > 1:
                raise ValueError("More than one round of measurement only needed with fault tolerant ancilla measurement")
        if not fault_tolerant_b:
            if not fault_tolerant_c:
                if data_rounds > 1:
                    raise ValueError("More than one round of measurement only needed with fault tolerant ancilla measurement")
        if fault_tolerant_b:
            if fault_tolerant_c:
                raise ValueError("Fault tolerant preparation of the logical qubit must follow scheme B or C2")
        validate_integer(ancilla_rounds)
        validate_integer(data_rounds)
        self.__d = d
        self.__ancilla = ancilla
        self.__extend_ancilla = extend_ancilla
        self.__fault_tolerant_b = fault_tolerant_b
        self.__fault_tolerant_c = fault_tolerant_c
        self.__fault_tolerant_ancilla = fault_tolerant_ancilla
        self.__num_ancilla_rounds = ancilla_rounds
        self.__num_data_rounds = data_rounds
        #number of data qubits is length of rows parity matrix 
        self.__num_data = len(parity_check_matrix[0])        
        #number of ancilla qubits is number of columns in the parity matrix.    
        self.__num_ancilla = len(parity_check_matrix)
        self.__num_extra_ancilla = 4        #four extra ancilla for decoding
        self.__num_ftc = 1                  #one ft ancilla for encoding in Scheme C
        self.__num_ft_anc = 4               # four fault tolerant ancilla
        self.__parity_check_matrix = parity_check_matrix
        self.__codewords = codewords
        self.__number_of_logical_qubits = d
        self.define_data()
        list_of_all_registers = self.define_registers(d)
        # extend quantum circuits
        super().__init__(*list_of_all_registers)
        self.validate_parity_matrix()

    def define_data(self):
        """define standing data
        
        Notes
        -----
        The ancilla qubits for the X operator are self.__mx
        The ancilla qubits for the Z operator are self.__mz

        There are more ancilla qubits if there are fault tolerant ancilla.  In this case the classical measurement bits can support 
        multiple rounds of measurement.

        Also, multiple classical rounds of measurement are supported for Goto's schemes b and c.  In scheme b
        the multiple classical rounds are only on the second qubit.
        """
        self.__data = []                    #data qubits
        if self.__fault_tolerant_b:
            # split out the second list item 
            # under scheme b repeated measurment is only needed of the second qubit
            self.__data_classical = [ [], [[] for i in range(self.__num_data_rounds)]]
        else:
            self.__data_classical = []
        if self.__fault_tolerant_c:
            self.__ftc = []
            self.__ftc_classical = [[] for i in range(self.__num_data_rounds)]
        if self.__ancilla:
            if self.__fault_tolerant_ancilla:
                self.__mx = [[] for i in range(self.__d)]
                self.__mz = [[] for i in range(self.__d)]
                self.__mx_classical = [[[] for i in range(self.__num_ancilla)] for j in range(self.__d) ]
                self.__mz_classical = [[[] for i in range(self.__num_ancilla)] for j in range(self.__d) ]
            else:
                self.__mx = []                      #ancilla qubits to detect X operator
                self.__mz = []                      #ancilla qubits to detect Z operator
                self.__mx_classical = []
                self.__mz_classical = []        
        if self.__extend_ancilla: 
            self.__extra_ancilla = []
            self.__extra_ancilla_classical = []

    def define_registers(self, d):
        """Set up registers used based on number of logical qubits and whether error checking is needed.

        Parameters
        ----------
        d : int
            Number of logical "data" qubits to be initialised. Should be either 0 or 1 at present.

        Notes
        -----
        The registers are stored in a list so that they can be indexed to simplify subsequent code.
        The registers required depends on the number of logical qubits, whether extra ancilla qubits
        are needed for error checking and the round of measurements needed.
        """
        list_of_all_registers = []
        for index1 in range(d):  
            #define label for logical qubits
            self.__qubit_no1 = str(index1)
            # Quantum registers
            self.__data.append(QuantumRegister(self.__num_data, "data " + self.__qubit_no1))
            list_of_all_registers.append(self.__data[index1])
            if self.__ancilla:
                if self.__fault_tolerant_ancilla:
                    for index2 in range(self.__num_ancilla):
                        self.__qubit_no2 = ' ' + str(index2)
                        self.__mx[index1].append(QuantumRegister(self.__num_ft_anc, "ancilla X " + self.__qubit_no1 
                                                                + self.__qubit_no2))
                        list_of_all_registers.append(self.__mx[index1][index2])
                    for index2 in range(self.__num_ancilla):
                        self.__qubit_no2 = ' ' + str(index2)
                        self.__mz[index1].append(QuantumRegister(self.__num_ft_anc, "ancilla Z " + self.__qubit_no1 
                                                                + self.__qubit_no2))
                        list_of_all_registers.append(self.__mz[index1][index2])
                else:
                    self.__mx.append(QuantumRegister(self.__num_ancilla, "ancilla X " + self.__qubit_no1))
                    self.__mz.append(QuantumRegister(self.__num_ancilla, "ancilla Z " + self.__qubit_no1))
                    list_of_all_registers.append(self.__mx[index1])
                    list_of_all_registers.append(self.__mz[index1])
            if self.__extend_ancilla: 
                self.__extra_ancilla.append(QuantumRegister(self.__num_extra_ancilla, name="extra ancilla" + self.__qubit_no1)) 
                list_of_all_registers.append(self.__extra_ancilla[index1])
            if self.__fault_tolerant_c:
               self.__ftc.append(QuantumRegister(self.__num_ftc, "fault tolerant " + self.__qubit_no1))
               list_of_all_registers.append(self.__ftc[index1])

            # Classical registers
            if self.__fault_tolerant_b:
                if index1 == 1:
                    #add three classical registers to allow for three measurements of second register
                    for index3 in range(self.__num_data_rounds):
                        self.__qubit_no3 = str(index3)
                        self.__data_classical[index1][index3] = (ClassicalRegister(self.__num_data, "measure_data " 
                                                                        + self.__qubit_no1 + self.__qubit_no3))                                          
                        list_of_all_registers.append(self.__data_classical[index1][index3])
                else:
                    self.__data_classical[index1] = (ClassicalRegister(self.__num_data, "measure_data " + self.__qubit_no1))
                    list_of_all_registers.append(self.__data_classical[index1])
            else:
                self.__data_classical.append(ClassicalRegister(self.__num_data, "measure_data " + self.__qubit_no1))
                list_of_all_registers.append(self.__data_classical[index1])
            if self.__fault_tolerant_c:
                for index3 in range(self.__num_data_rounds):
                        self.__qubit_no3 = str(index3)
                        self.__ftc_classical[index1].append(ClassicalRegister(self.__num_ftc, "measure_ft_data " 
                                                                        + self.__qubit_no1 + self.__qubit_no3))                                         
                        list_of_all_registers.append(self.__ftc_classical[index1][index3])
            if self.__ancilla:
                if self.__fault_tolerant_ancilla:
                        for index2 in range(self.__num_ancilla):
                            for index3 in range(self.__num_ancilla_rounds):
                                self.__qubit_no2 = str(index2)
                                self.__qubit_no3 = str(index3)
                                self.__mx_classical[index1][index2].append(ClassicalRegister(self.__num_ft_anc, "measure_ancilla_X "
                                                                    + self.__qubit_no1 + self.__qubit_no2 + self.__qubit_no3))
                                list_of_all_registers.append(self.__mx_classical[index1][index2][index3])
                        for index2 in range(self.__num_ancilla):
                            for index3 in range(self.__num_ancilla_rounds):
                                self.__qubit_no2 = str(index2)
                                self.__qubit_no3 = str(index3)
                                self.__mz_classical[index1][index2].append(ClassicalRegister(self.__num_ft_anc, "measure_ancilla_Z " 
                                                                    + self.__qubit_no1 + self.__qubit_no2 + self.__qubit_no3))
                                list_of_all_registers.append(self.__mz_classical[index1][index2][index3])
                else:
                    self.__mx_classical.append(ClassicalRegister(self.__num_ancilla, "measure_ancilla_X " + self.__qubit_no1))
                    self.__mz_classical.append(ClassicalRegister(self.__num_ancilla, "measure_ancilla_Z " + self.__qubit_no1))
                    list_of_all_registers.append(self.__mx_classical[index1]) 
                    list_of_all_registers.append(self.__mz_classical[index1])
            if self.__extend_ancilla: 
                self.__extra_ancilla_classical.append(
                    ClassicalRegister(self.__num_extra_ancilla, "measure_extra_ancilla " + self.__qubit_no1))
                list_of_all_registers.append(self.__extra_ancilla_classical[index1]) 
        return (list_of_all_registers)
    
    def validate_parity_matrix(self):
        """Validate the parity matrix against the allowed codewords"""
        if self.__parity_check_matrix == []:
            raise ValueError('Parity check matrix must be specified')
        
        for parity_string in self.__parity_check_matrix:
            if len(parity_string) != self.__num_data:
                raise ValueError('Parity check matrix rows incorrect length')
        if self.__ancilla:
            if len(self.__parity_check_matrix) != self.__num_ancilla:
                raise ValueError('Parity check matrix has incorrect number of rows')
        for codeword_string in self.__codewords:
            if len(codeword_string) != self.__num_data:
                raise ValueError("Code word rows incorrect length")
            for parity_string in self.__parity_check_matrix:
                bit_store = False
                for codeword_bit_string in codeword_string:
                    if codeword_bit_string not in ['0','1']:
                        raise ValueError("Code word entries must be 0 or 1")
                    for parity_bit_string in parity_string:
                        if parity_bit_string not in ['0','1']:
                            raise ValueError("Parity matrix entries must be 0 or 1")
                        bit_store = bit_store ^ bool(int(codeword_bit_string)) ^ bool(int(parity_bit_string))
                if bit_store:
                    raise ValueError("Code word rows must be orthogonal to the parity matrix")

    def set_up_logical_zero(self, logical_qubit = 0, reduced = True):
        """Set up logical zero for data qubit

        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to initialise. Should be either 0 or 1 at present.
        reduced : bool
            Checks to see if any gates are duplicated

        Notes
        -----
            Columns of the parity matrix with only one entry are prepared in the |+> state.
            CNOT gates from these |+> state to the parity matrix entries in the same row which are unity.  

            If reduced = True possible unnecessary duplicate CNOT gates are identified.  If possible two CNOT gates are removed and replaced by one 
            new CNOT gates.
        """
        self._validate_logical_qubit_number(logical_qubit)
        
        parity_matrix_totals = [ 0 for x in range(self.__num_data)] # define an empty list ready to work out parity_matrix_totals

        for parity_string in self.__parity_check_matrix:
            for index in range(self.__num_data):
                parity_matrix_totals[index] = parity_matrix_totals[index] + int(parity_string[index])
        count = 0

        if reduced:
            #find duplicated entries
            duplicate_entries = []
            for column_index1 in range(self.__num_ancilla):
                parity_row1 = self.__parity_check_matrix[column_index1]
                for bit_index in range(self.__num_data):                
                    if parity_matrix_totals[bit_index] == 1 and parity_row1[bit_index] == '1':
                        h_qubit1 = bit_index
                for column_index2 in range(column_index1 + 1, self.__num_ancilla, 1):
                    parity_row2 = self.__parity_check_matrix[column_index2]
                    for bit_index in range(self.__num_data):
                        if parity_matrix_totals[bit_index] == 1 and parity_row2[bit_index] == '1':
                            h_qubit2 = bit_index
                    h_qubit_start = max(h_qubit1, h_qubit2)
                    for bit_index in range(h_qubit_start + 1, self.__num_data):
                        bit1 = parity_row1[bit_index]
                        bit2 = parity_row2[bit_index]
                        if bit1 == '1' and bit2 == '1':
                            duplicate_entries.append([[h_qubit1, bit_index], [h_qubit2, bit_index]])

        #specify that each bit is zero
        #put entries into cx_gates for each CNOT based on relevant entry in the parity matrix
        cx_gates = []
        for index in range (self.__num_data):
            self.reset(self.__data[logical_qubit][index])  
                #specify that each bit is zero
            if parity_matrix_totals[index] == 1:
                count = count + 1
                #set up |+> state if count is one
                self.h(self.__data[logical_qubit][index])
                for parity_row in self.__parity_check_matrix:
                    # from the |+> state qubits build the rest of the ancilla.
                    if parity_row[index] == '1':             
                        for column_number in range(self.__num_data):
                            if column_number != index:
                                if parity_row[column_number] == '1':
                                    #cx from |+> state to qubit if there is a 1 in the parity matrix.
                                    cx_gates.append([index,column_number])
        if count != self.__num_ancilla:
            raise ValueError(f'Unable to construct matrix as parity matrix does not match the ancilla needed.  Count = {count}')   
        removed_gates = []
        if reduced:
            #if duplicate entries remove two gates and add one new gate pair
            cx_gates_added = []
            #cx_gates holds the list of cx_gates to replace those deleted
            number_of_duplicates = len(duplicate_entries)
            if (number_of_duplicates % 2) != 0:
                raise ValueError(f'Expect an even number of entries in the duplicates. {number_of_duplicates} entries found')
            for index in range(int(number_of_duplicates / 2)):
                support = duplicate_entries[2 * index]
                duplicates = duplicate_entries[2 * index + 1]
                if duplicates[0] in cx_gates and duplicates[1] in cx_gates:
                    #check if any of the cx_gates can be removed
                    if duplicates[0] not in removed_gates and duplicates[1] not in removed_gates:
                        for i in range(2):
                            removed_gates.append(duplicates[i])
                            if duplicates[0][1] != duplicates[1][1]:
                                raise ValueError('Error removing duplicates from parity matrix')
                            if support[0][1] != support[1][1]:
                                raise ValueError('Error removing duplicates from parity matrix')
                        cx_gates_added.append([support[0][1], duplicates[0][1]])
        for items in cx_gates:
            if items not in removed_gates:
                index = items[0]
                column_number = items[1]
                self.cx(self.__data[logical_qubit][index],self.__data[logical_qubit][column_number])
        if reduced:
            for items in cx_gates_added:
                index = items[0]
                column_number = items[1]
                self.cx(self.__data[logical_qubit][index],self.__data[logical_qubit][column_number])

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
            The ancilla needed are determined from the parity matrix.  Fault tolerant logic is included to use four 
            ancilla qubits, set these up in a GHZ, and then apply a CZ gate to each one individually.
        """
        self._validate_logical_qubit_number(logical_qubit)
        #specify that each bit is zero
        for index in range (self.__num_ancilla):
            if self.__fault_tolerant_ancilla:
                for index2 in range(self.__num_ft_anc):
                    self.reset(self.__mx[logical_qubit][index][index2])
                    self.reset(self.__mz[logical_qubit][index][index2])
            else:   
                self.reset(self.__mx[logical_qubit][index])  
                self.reset(self.__mz[logical_qubit][index])  
        self.barrier()
        #set up hadamards
        if self.__fault_tolerant_ancilla:
            for index in range (self.__num_ancilla):
                self.h(self.__mx[logical_qubit][index][0])
                self.h(self.__mz[logical_qubit][index][0])
        else:
            self.h(self.__mx[logical_qubit])
            self.h(self.__mz[logical_qubit])
        self.barrier()
        if self.__fault_tolerant_ancilla:
            #set up GHZ state
            for index in range (self.__num_ancilla):
                for index2 in range(self.__num_ft_anc - 1):
                    self.cx(self.__mx[logical_qubit][index][index2], 
                            self.__mx[logical_qubit][index][index2 + 1])
                    self.cx(self.__mz[logical_qubit][index][index2], 
                            self.__mz[logical_qubit][index][index2 + 1])
            self.barrier()

        #apply CX gates according to the parity matrix
        if self.__fault_tolerant_ancilla:
            #lists to keep count of which sub-ancilla to use next
            next_x_ancilla = [0 for index in range(self.__num_ancilla)]
            next_z_ancilla = [0 for index in range(self.__num_ancilla)]
        for index in range (self.__num_ancilla):
            parity_row = self.__parity_check_matrix[index]
            for column_number in range(self.__num_data):
                if parity_row[column_number] == '1':
                    if self.__fault_tolerant_ancilla:
                        #for index2 in range(self.__num_ft_anc):
                        index2 = next_x_ancilla[index]
                        self.cx(self.__mx[logical_qubit][index][index2],
                                self.__data[logical_qubit][column_number])    
                        next_x_ancilla[index] = next_x_ancilla[index] + 1  
                    else:
                        self.cx(self.__mx[logical_qubit][index],self.__data[logical_qubit][column_number])  
        self.barrier()
        #apply CZ gates according to the parity matrix
        #done separately so Qiskit diagram is easier to review
        for index in range (self.__num_ancilla):
            parity_row = self.__parity_check_matrix[index]
            for column_number in range(self.__num_data):
                if parity_row[column_number] == '1':     
                    if self.__fault_tolerant_ancilla:
                        index2 = next_z_ancilla[index]
                        self.cz(self.__mz[logical_qubit][index][index2],
                                self.__data[logical_qubit][column_number])      
                        next_z_ancilla[index] = next_z_ancilla[index] + 1  
                    else:
                        self.cz(self.__mz[logical_qubit][index],self.__data[logical_qubit][column_number])  
        self.barrier()
 
        if self.__fault_tolerant_ancilla:
        #un-encode set up GHZ state
            for index in range (self.__num_ancilla):
                for index2 in range(self.__num_ft_anc - 1, 0, -1):
                    self.cx(self.__mx[logical_qubit][index][index2 - 1], 
                            self.__mx[logical_qubit][index][index2])
                    self.cx(self.__mz[logical_qubit][index][index2 - 1], 
                            self.__mz[logical_qubit][index][index2])
        self.barrier()
        #set up hadamards
        if self.__fault_tolerant_ancilla:
            for index in range (self.__num_ancilla):
                self.h(self.__mx[logical_qubit][index][0])
                self.h(self.__mz[logical_qubit][index][0])
        else:
            self.h(self.__mx[logical_qubit])
            self.h(self.__mz[logical_qubit])
        self.barrier()

    def logical_measure_data(self, logical_qubit = 0, measure_round = 1):
        """Makes measurement of the data qubits of a logical qubit.

        Parameters
        ----------
        logical_qubit : int
            Number of the logical "data" qubits to measure. Should be either 0 or 1 at present.
        measure_round : int
            Round of data measurement.  Can be more than one for scheme B or C.

        Notes
        -----
        For Scheme B there are normally three rounds of measuremement for the second logical qubit and three classical measurement bits are created,
        one for each round.  For Scheme C there are also normally three rounds of measurement.
        """
        self._validate_logical_qubit_number(logical_qubit)
        #need to measure the ancilla for each round
        validate_integer(measure_round)

        for index in range(self.__num_data):
            if self.__fault_tolerant_b:
                if logical_qubit == 1:
                    round_index = measure_round - 1
                    self.measure(self.__data[logical_qubit][index], 
                                self.__data_classical[logical_qubit][round_index][index])  
                else:
                    self.measure(self.__data[logical_qubit][index], 
                                self.__data_classical[logical_qubit][index])
            elif self.__fault_tolerant_c:
                if measure_round == self.__num_data_rounds:
                    #final round only - measure all qubits
                    self.measure(self.__data[logical_qubit][index], 
                                self.__data_classical[logical_qubit][index])
            else:
                self.measure(self.__data[logical_qubit][index], 
                            self.__data_classical[logical_qubit][index])
        if self.__fault_tolerant_c:
            if measure_round > self.__num_data_rounds:
                raise ValueError (f'Data measurement qubits for only {self.__num_data_rounds} round(s) are available')
            measure_index = measure_round - 1
            for index in range(self.__num_ftc):
                self.measure(self.__ftc[logical_qubit][index],
                        self.__ftc_classical[logical_qubit][measure_index][index]) 
        
    def logical_measure_ancilla(self, logical_qubit = 0, ancilla_round = 1):
        """Makes measurement of the ancilla qubits of a logical qubit.

            Parameters
            ----------
            logical_qubit : int
                Number of the logical "data" qubits to measure. 
                Should be either 0 or 1 at present.
            ancilla_round : int
                Round of ancilla measurement.  
                Can be more than one for fault tolerant ancilla.

            Notes
            -----
            If there is more than one ancilla_round the classical 
            measurements bit created above can be used.
            For example, if there are three rounds of measuremement 
            three classical measurement bits are created,
            one for each round.
        """

        if not self.__ancilla:
            raise ValueError('No qubits set up for ancilla measurements')
        self._validate_logical_qubit_number(logical_qubit)
        #need to measure the ancilla for each round
        validate_integer(ancilla_round)
        if ancilla_round > self.__num_ancilla_rounds:
            raise ValueError (f'Ancilla measurement qubits for only {self.__num_ancilla_rounds} round(s) are available')
        round_index = ancilla_round - 1
        if self.__fault_tolerant_ancilla:
            for index1 in range(self.__num_ancilla): 
                for index2 in range(self.__num_ft_anc):
                    self.measure(self.__mx[logical_qubit][index1][index2], 
                            self.__mx_classical[logical_qubit][index1][round_index][index2])
                    self.measure(self.__mz[logical_qubit][index1][index2], 
                            self.__mz_classical[logical_qubit][index1][round_index][index2])
        else:
            for index1 in range(self.__num_ancilla):
                self.measure(self.__mx[logical_qubit][index1], 
                            self.__mx_classical[logical_qubit][index1])
                self.measure(self.__mz[logical_qubit][index1], 
                            self.__mz_classical[logical_qubit][index1])
        self.barrier()
        if ancilla_round == 1:
            #only need to measure extended ancilla qubits once
            if self.__extend_ancilla:
                for index in range(self.__num_extra_ancilla):
                    self.measure(self.__extra_ancilla[logical_qubit][index], 
                                self.__extra_ancilla_classical[logical_qubit][index])

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

            The errors detected by the Z operators are bit flips, so are corrected by CX gates.
            The errors detected by the X operators are phase flips, so are corrected by CZ gates.

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
                if bits == '1':
                    count = count + 1
            qubit_data.update({qubit:{"count":count}})

        if mct:
            for qubit in range(self.__num_data):
                bit_list = transpose_parity[qubit]
                #x ancilla errors
                #flip zero ancilla bit to one
                for bit_index in range(self.__num_ancilla): 
                    if bit_list[bit_index] == '0':
                        self.x(self.__mz[logical_qubit][bit_index])
                # use MCT gate to bit flip incorrect qubit
                self.mct([self.__mz[logical_qubit][0], 
                              self.__mz[logical_qubit][1], 
                              self.__mz[logical_qubit][2]],
                              self.__data[logical_qubit][qubit])
                #flip zero ancilla bits back
                for bit_index in range(self.__num_ancilla): 
                    if bit_list[bit_index] == '0':
                        #bit flip identified with Z logical operator corrected with bit flip
                        self.x(self.__mz[logical_qubit][bit_index])

                #z ancilla errors
                #flip zero ancilla bit to one
                for bit_index in range(self.__num_ancilla): 
                    if bit_list[bit_index] == '0':
                        #bit flip identified with Z logical operator corrected with bit flip
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
                    if bit_list[bit_index] == '0':
                        self.x(self.__mx[logical_qubit][bit_index])
                
        else:
            for qubit in range(self.__num_data):
                bit_list = transpose_parity[qubit]
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")      
                if count == 1:
                    for bit_index in range(self.__num_ancilla): 
                        if bit_list[bit_index] == '1':
                            self.cx(self.__mz[logical_qubit][bit_index], 
                                    self.__data[logical_qubit][qubit])    
                            single_CX_updates_list.append([qubit, bit_index])
                            self.cz(self.__mx[logical_qubit][bit_index], 
                                    self.__data[logical_qubit][qubit]) 
                            
            extra_ancilla = 0   
            for qubit in range(self.__num_data):
                bit_list = transpose_parity[qubit]
                qubit_data_item = qubit_data.get(qubit)
                count = qubit_data_item.get("count")           
                if count == 2:      
                    for bit_index in range(self.__num_ancilla): 
                        first_bit = '0'
                        second_bit = '0'   
                        if count == 2:   # need a CCNOT gate
                            for bit_index in range(self.__num_ancilla): 
                                if bit_list[bit_index] == '1':
                                    if first_bit == '0':
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
                    #need to undo impact of all gates made earlier 
                    #as odd parity by inspection of codes.
                    #maybe later could add code to check the changes made, 
                    #and show they have odd parity.
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
                        first_bit = '0'
                        second_bit = '0'   
                        if count == 2:   # need a CCNOT gate
                            for bit_index in range(self.__num_ancilla): 
                                if bit_list[bit_index] == '1':
                                    if first_bit == '0':
                                        first_bit = bit_index
                                    else:
                                        second_bit = bit_index
                ## need to add a ccx gate
                    self.ccx(self.__mz[logical_qubit][first_bit], 
                            self.__mz[logical_qubit][second_bit], 
                            self.__extra_ancilla[logical_qubit][extra_ancilla])
                    extra_ancilla = extra_ancilla + 1

    def decode(self, logical_qubit = 0, reduced = True):
        """Uncomputer setting up logical zero for data qubit.  This is a reversal of the encoding circuit.

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to set up logical zero for. Should be either 0 or 1 at present.
            reduced : bool
                Checks to see if any gates are duplicated    

            Notes
            -----
            The gates needed are determined from the parity matrix.
        """
        self._validate_logical_qubit_number(logical_qubit)
        parity_matrix_totals = [ 0 for x in range(self.__num_data)] 
        # define an empty list ready to work out parity_matrix_totals

        for parity_string in self.__parity_check_matrix:
            for index in range(self.__num_data):
                parity_matrix_totals[index] = parity_matrix_totals[index] + int(parity_string[index])
        count = 0

        if reduced:
            #find duplicated entries
            duplicate_entries = []
            for column_index1 in range(self.__num_ancilla):
                parity_row1 = self.__parity_check_matrix[column_index1]
                for bit_index in range(self.__num_data):                
                    if parity_matrix_totals[bit_index] == 1 and parity_row1[bit_index] == '1':
                        h_qubit1 = bit_index
                for column_index2 in range(column_index1 + 1, self.__num_ancilla, 1):
                    parity_row2 = self.__parity_check_matrix[column_index2]
                    for bit_index in range(self.__num_data):
                        if parity_matrix_totals[bit_index] == 1 and parity_row2[bit_index] == '1':
                            h_qubit2 = bit_index
                    h_qubit_start = max(h_qubit1, h_qubit2)
                    for bit_index in range(h_qubit_start + 1, self.__num_data):
                        bit1 = parity_row1[bit_index]
                        bit2 = parity_row2[bit_index]
                        if bit1 == '1' and bit2 == '1':
                            duplicate_entries.append([[h_qubit1, bit_index], [h_qubit2, bit_index]])

        #specify that each bit is zero
        #put entries into cx_gates for each CNOT based on 
        #relevant entry in the parity matrix
        cx_gates = []
        for index in range (self.__num_data):
            #specify that each bit is zero
            if parity_matrix_totals[index] == 1:
                count = count + 1
                #set up |+> state if count is one
                for parity_row in self.__parity_check_matrix:
                    # from the |+> state qubits build the rest of the ancilla.
                    if parity_row[index] == '1':             
                        for column_number in range(self.__num_data):
                            if column_number != index:
                                if parity_row[column_number] == '1':
                                    #cx from |+> state to qubit 
                                    #if there is a 1 in the parity matrix.
                                    cx_gates.append([index,column_number])
        if count != self.__num_ancilla:
            raise ValueError(f'Unable to construct matrix as parity matrix does not match the ancilla needed.  Count = {count}')   
        removed_gates = []
        if reduced:
            #if duplicate entries remove two gates and add one new gate pair
            cx_gates_added = []
            #cx_gates holds the list of cx_gates to replace those deleted
            number_of_duplicates = len(duplicate_entries)
            if (number_of_duplicates % 2) != 0:
                raise ValueError(f'Expect an even number of entries in the duplicates. {number_of_duplicates} entries found')
            for index in range(int(number_of_duplicates / 2)):
                support = duplicate_entries[2 * index]
                duplicates = duplicate_entries[2 * index + 1]
                if duplicates[0] in cx_gates and duplicates[1] in cx_gates:
                    #check if any of the cx_gates can be removed
                    if duplicates[0] not in removed_gates and duplicates[1] not in removed_gates:
                        for i in range(2):
                            removed_gates.append(duplicates[i])
                            if duplicates[0][1] != duplicates[1][1]:
                                raise ValueError('Error removing duplicates from parity matrix')
                            if support[0][1] != support[1][1]:
                                raise ValueError('Error removing duplicates from parity matrix')
                        cx_gates_added.append([support[0][1], duplicates[0][1]])
        if reduced:
            for items in cx_gates_added:
                index = items[0]
                column_number = items[1]
                self.cx(self.__data[logical_qubit][index],
                        self.__data[logical_qubit][column_number])
        for items in cx_gates:
            if items not in removed_gates:
                index = items[0]
                column_number = items[1]
                self.cx(self.__data[logical_qubit][index],
                        self.__data[logical_qubit][column_number])
        for index in range (self.__num_data):
            if parity_matrix_totals[index] == 1:
                self.h(self.__data[logical_qubit][index])

    def logical_gate_X(self, logical_qubit = 0):
        """Apply a logical X gate

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to apply logical X gate to. 
                Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit = 0)
        for index in range(self.__num_data):
            self.x(self.__data[logical_qubit][index])

    def logical_gate_H(self, logical_qubit = 0):
        """Apply a logical H gate

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to apply Hadamard on. 
                Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__num_data):
            self.h(self.__data[logical_qubit][index])

    def logical_gate_Z(self, logical_qubit = 0):
        """Apply a logical Z gate

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to apply logical Z gate on. 
                Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__num_data):
            self.z(self.__data[logical_qubit][index])
    
    def logical_gate_CX(self, logical_control_qubit, logical_target_qubit):
        """Apply a logical CX gate
            
            Parameters
            ----------

                logical_control_qubit : int
                    Number of the logical "data" qubit 
                    which controls the CX gate
                logical_target_qubit : int
                    Number of the logical "data" qubit 
                    which is the target for the CX gate
        """
        self._validate_logical_qubit_number(logical_control_qubit)
        self._validate_logical_qubit_number(logical_target_qubit)
        if logical_control_qubit == logical_target_qubit:   
            raise ValueError("the control and target qubits for the logical CX must be different")
        for index in range(self.__num_data):
            self.cx(self.__data[logical_control_qubit][index], 
                    self.__data[logical_target_qubit][index])
    
    def dummy_decoding(self, input_string, logical_qubit = 0):
        """Instead of the full decoding circuit a dummy circuit 
        is set up for testing.
        
        Parameters
        ----------

            input_string : str
                String to control gates set up
            logical_qubit: int
                Number of the logical "data" qubits to apply logical Z gate on. 
                Should be either 0 or 1 at present.

        Notes
        -----
        This function is not currently used by any workbook but is 
        retained in case it is useful in future.
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
        """Validates the logical qubit number.  
        Code might be enhanced in the future.

            Parameters:
            -----------

            logical_qubit : int
                Number of the logical "data" qubit to check
        """
        validate_integer(logical_qubit)
        if logical_qubit > self.__d:
            raise ValueError("Logical operations must be on qubits initialised")
        if logical_qubit < 0:
            raise ValueError("Logical qubit number must be positive")

    def _validate_physical_qubit_number(self, physical_qubit):
        """ Validate the physical qubit number 

            Parameters
            ----------
            physical qubit : int
                Number of the physical qubit to validate
        """        
        validate_integer(physical_qubit)
        if physical_qubit > self.__num_data - 1 :
            raise ValueError("Qubit index must be in range of data qubits")
        if physical_qubit < 0:
            raise ValueError("Qubit index must be in range of data qubits")

    def list_data_qubits(self):
        """ Returns a list of data qubits

        Returns
        -------
        output_list : list
            list of data qubits
        """         

        output_list = []
        for logical_qubit in range(self.__number_of_logical_qubits):
            list_for_one_logical_qubit = []
            for physical_qubit in range(self.__num_data):
                data_qubit = self.__data[logical_qubit][physical_qubit]
                print(data_qubit)
                list_for_one_logical_qubit.append(data_qubit)
            output_list.append(list_for_one_logical_qubit)
        return(output_list)

    def encode_fault_tolerant_method_C(self, control_qubits, logical_qubit = 0):
        """use a new qubit to encode fault tolerantly

            Parameters
            ----------
            logical_qubit: int
                Number of the logical "data" qubits to encode fault tolerantly. 
                Should be either 0 or 1 at present.
            control_qubits: list
                List of control qubits
            

            Notes
            -----
            Uses Goto's method C
        """
        self._validate_logical_qubit_number(logical_qubit)
        #reset
        for index in range(self.__num_ftc):
            self.reset(self.__ftc[logical_qubit][0])
        for qubit in control_qubits:
            self.cx(self.__data[logical_qubit][qubit], 
                    self.__ftc[logical_qubit][0])
        
class BaconShorCodeLogicalQubit(QuantumCircuit):
    """Generates the gates for one logical Qubits of the Bacon Shor code

        Parameters
        ----------
        d : int
            Number of logical "data" qubits to be initialised. 
            Should be either 1 or 2 at present.
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

    def __init__(self, d, data_qubits, ancilla_qubits, ancillas, 
                blocks, logical_one, logical_z):
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
        """Set up registers used based on number of logical qubits 
        and whether error checking is needed.

        Parameters
        ----------
        d : int
            Number of the logical "data" qubits to be initialised. 
            Should be either 0 or 1 at present.
        
        Notes
        -----
        The registers are stored in a list so that they can be 
        indexed to simplify subsequent code.

        """
        list_of_all_registers = []
        for index in range(d):
            self.__qubit_no = str(index)
            # Quantum registers
            self.__data.append(QuantumRegister(self.__data_qubits, 
                        "data " + self.__qubit_no))
            self.__ancilla.append(QuantumRegister(self.__ancilla_qubits, 
                        "ancilla "+ self.__qubit_no))
            list_of_all_registers.append(self.__data[index])
            list_of_all_registers.append(self.__ancilla[index])

            # Classical registers
            self.__data_classical.append(ClassicalRegister(self.__data_qubits, 
                                        "measure_data " + self.__qubit_no))
            self.__ancilla_classical.append(ClassicalRegister(self.__ancilla_qubits, 
                                            "measure_ancilla "+ self.__qubit_no) )
            list_of_all_registers.append(self.__data_classical[index])
            list_of_all_registers.append(self.__ancilla_classical[index]) 
        return (list_of_all_registers)

    def encoding_nft(self, logical_qubit = 0,):
        """ Adds an encoding non fault tolerant gate.  
        
        Parameters
        ----------
        logical_qubit: int
            Number of the logical "data" qubit to encode. 
            Should be either 0 or 1 at present.
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
            Number of the logical "data" qubit to encode. 
            Should be either 0 or 1 at present.
        """
        self._validate_logical_qubit_number(logical_qubit)
        for count in range(self.__blocks):
            first_qubit = count * self.__blocks
            second_qubit = count * self.__blocks + 1
            third_qubit = count * self.__blocks + 2
            self.h(self.__data[logical_qubit][first_qubit])
            self.cx(self.__data[logical_qubit][first_qubit],
                    self.__data[logical_qubit][second_qubit])
            self.cx(self.__data[logical_qubit][first_qubit],
                    self.__data[logical_qubit][third_qubit])
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
            Number of the logical "data" qubit to test. 
            Should be either 0 or 1 at present.
        
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
            Number of the logical "data" qubit to test. 
            Should be either 0 or 1 at present.
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
            Number of the logical "data" qubit to set up ancilla for. 
            Should be either 0 or 1 at present.
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
            Number of the logical "data" qubit to set up ancilla for. 
            Should be either 0 or 1 at present.
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
            Number of the logical "data" qubit to measure. 
            Should be either 0 or 1 at present.
        """

        self._validate_logical_qubit_number(logical_qubit)
        for index in range(self.__data_qubits):
            self.measure(self.__data[logical_qubit][index], 
                        self.__data_classical[logical_qubit][index])
        for index in range(self.__ancilla_qubits):
            self.measure(self.__ancilla[logical_qubit][index], 
                        self.__ancilla_classical[logical_qubit][index])

    def _validate_logical_qubit_number(self, logical_qubit):
        """Validates the logical qubit number.  
        Code might be enhanced in the future.

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
        validate_integer(physical_qubit)
        if physical_qubit > self.__data_qubits - 1 :
            raise ValueError("Qubit index must be in range of data qubits")
        if physical_qubit < 0:
            raise ValueError("Qubit index must be in range of data qubits")