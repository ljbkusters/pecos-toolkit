import collections
import itertools

import pecos

# Error types and gate symbols
_IDENTITY = {"I"}
_PAULI_X = {"X"}
_PAULI_Y = {"Y"}
_PAULI_Z = {"Z"}
_PAULI_ERRORS = {*_PAULI_X, *_PAULI_Y, *_PAULI_Z}
_PAULI_GROUP = {*_IDENTITY, *_PAULI_ERRORS}
_PAULI_ERROR_TWO = set(itertools.permutations(  # all pairwise permutations
                        list(_PAULI_ERRORS) + list(_PAULI_GROUP), 2))

# circuit inits
_INITS_X = {"init |+>", "init |->"}
_INITS_Y = {"init |+i>", "init |-i>"}
_INITS_Z = {"init |0>", "init |1>"}
_INITS_ALL = {*_INITS_X, *_INITS_Y, *_INITS_Z}

# circuit elements
_HADAMARDS = {'H', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H+z+x', 'H-z-x',
              'H+y-z', 'H-y-z', 'H-x+y', 'H-x-y'}
_Q_GATES = {'Q', 'Qd'}  # X -> X, Z -> +/- Y
_S_GATES = {'S', 'Sd'}  # X -> +/- Y, Z -> Z
_ROTATIONS = {'R', 'Rd', 'RX', 'RY', 'RZ'}
_OCTAHEDRON_ROTATIONS = {'F1', 'F1d', 'F2', 'F2d', 'F3', 'F3d', 'F4', 'F4d'}
_ONE_QUBIT_GATES = {*_PAULI_GROUP, *_Q_GATES, *_S_GATES,
                    *_HADAMARDS, *_OCTAHEDRON_ROTATIONS, *_ROTATIONS}
_TWO_QUBIT_GATES = {'CNOT', 'CZ', 'SWAP', 'G', 'MS', 'SqrtXX', 'RXX'}

# circuit measurements
_MEASURE_X = {"measure X"}
_MEASURE_Y = {"measure Y"}
_MEASURE_Z = {"measure Z"}
_MEASURE_ALL = {*_MEASURE_X, *_MEASURE_Y, *_MEASURE_Z}

# named tuple type factories
GateError = collections.namedtuple("_GATE_ERROR", ("error_param", "after"))

ErrorProneGateCollection = collections.namedtuple("_ErrorProneGateCollection",
                                                  ("symbol", "ep_gates",
                                                   "param", "error_gates",
                                                   "before", "after"))
IdleErrorCollection = collections.namedtuple("_IdleErrorCollection",
                                             ("symbol", "param", "error_gates",
                                              "before", "after"))

# Basic EPGCs
FlipZInit = ErrorProneGateCollection(
                symbol="init_z",
                ep_gates={"init |0>", "init |1>"},
                param="init", error_gates={"X"},
                before=False, after=True,
                )
FlipXInit = ErrorProneGateCollection(
                symbol="init_x",
                ep_gates={"init |+>", "init |->"},
                param="init", error_gates={"Z"},
                before=False, after=True,
                )
FlipZMeasurement = ErrorProneGateCollection(
                symbol="measure_x",
                ep_gates={"measure Z"},
                param="meas", error_gates={"X"},
                before=True, after=False,
                )
FlipXMeasurement = ErrorProneGateCollection(
                symbol="measure_x",
                ep_gates={"measure X"},
                param="meas", error_gates={"Z"},
                before=True, after=False,
                )


class __BaseErrorGen(pecos.error_gens.parent_class_error_gen.ParentErrorGen):
    """Code capacity gen based on ParentErrorGen"""

    def __init__(self, *args, **kwargs):
        """"""
        self.error_prone_gates = None
        super().__init__()
        self.gen = self.generator_class()
        self.configure_error_generator(*args, **kwargs)

    def configure_error_generator(self, *args, **kwargs):
        """Configure the error generator (self.gen)

        This is where the main bulk of the initialization takes place.
        This class abstracts this step into its own method such that
        the user no longer has to touch the __init__ method unless
        something else has to be initialized.

        The method should always be overloaded.
        """
        raise NotImplementedError("The method 'configure_error_generator'"
                                  " should be overloaded by inheriting classes"
                                  " but wasn't for this class ('{}')"
                                  .format(type(self).__name__))

    def start(self, circuit, error_params, state):
        """Wrapper for new start function accepting state paramater"""
        return super().start(circuit, error_params)

    def generate_tick_errors(self, tick_circuit, time, **params):
        """
        Returns before errors, after errors, and replaced locations for
        the given key (args).

        The method should always be overloaded.

        Returns:
            set of error circuits
        """
        raise NotImplementedError("The method 'generate_tick_errors' should be"
                                  " overloaded by inheriting classes but"
                                  " wasn't for this class ('{}')"
                                  .format(type(self).__name__))

    def __repr__(self):
        return self.error_prone_gates


class GeneralErrorGen(__BaseErrorGen):

    ALLOWED_EPGC_TYPES = (ErrorProneGateCollection, IdleErrorCollection)

    def configure_error_generator(self, epgc_list=None):
        """Configure the error generator

        The kwargs defined above should be passed at init time, or by
        calling this method after init time with the proper parameters

        Args:
            error_types, set of gates (like {"X", "Y", "Z"})
            error_prone_gates, list of ErrorProneGateCollecion tracks
                which gates are error prone
        """
        if epgc_list is None:
            self.error_prone_gates = self.gen_error_prone_gates()
        else:
            self.error_prone_gates = epgc_list
        self.handle_error_prone_gates(self.error_prone_gates)

    @staticmethod
    def gen_error_prone_gates():
        return [ErrorProneGateCollection(symbol="init", ep_gates=_INITS_ALL,
                                         param="r",
                                         error_gates=_PAULI_ERRORS,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="one qubit",
                                         ep_gates=_ONE_QUBIT_GATES,
                                         param="p",
                                         error_gates=_PAULI_ERRORS,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="two qubit",
                                         ep_gates=_TWO_QUBIT_GATES,
                                         param="q",
                                         error_gates=_PAULI_ERRORS,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="measure",
                                         ep_gates=_MEASURE_ALL,
                                         param="s",
                                         error_gates=_PAULI_ERRORS,
                                         before=True, after=False),
                IdleErrorCollection(symbol="idle", param="i",
                                    error_gates=_PAULI_ERRORS,
                                    before=False, after=True),
                ]

    def handle_error_prone_gates(self, epgc_list, clear_generator=False):
        """Handle error_gen init from ErrorProneGateCollection objects

        This method implements the automatic initialization of all objects
        in the error_prone_gates list, which should ocntain exclusively
        ErrorProngeGateCollection (epgc) objects or by exception for
        idle errors which do not specify gates to operate on but act only
        on idle qubits IdleErrorCollection (iec).

        the handle_error_prone_gates method may also take a new list of
        error prone gates. If clear_generator is set to True, the error
        generator is fully reset, basically fully changing the way errors
        are generated to the new list of supplied epgc_list.

        Args:
            epgc_list, list of ErrorProneGateCollection objects
            clear_generator, bool to fully reset the generator object
        """
        types = self.ALLOWED_EPGC_TYPES
        if not isinstance(epgc_list, list):
            type_ = type(epgc_list).__name__
            raise TypeError(f"epgc_list should be of type list but is of type"
                            f" {type_}")
        if not all([isinstance(epgc, types) for epgc in epgc_list]):
            types = set([type(x).__name__ for x in epgc_list])
            raise TypeError("epgc_list should be list of "
                            "ErrorProneGateCollection or IldeErrorCollection"
                            f" objects but contains the types: {types}")

        if clear_generator:
            self.gen = self.generator_class()
        self.epgc_list = epgc_list
        self.errors = {}
        for epgc in self.epgc_list:
            if isinstance(epgc, ErrorProneGateCollection):
                self.gen.set_gate_group(epgc.symbol, epgc.ep_gates)
                # the cases below can be simultaniously configured
                if epgc.before is True:
                    self.configure_error_group(epgc, after=False)
                if epgc.after is True:
                    self.configure_error_group(epgc, after=True)
            elif isinstance(epgc, IdleErrorCollection):
                err = self.gen.ErrorSet(epgc.error_gates, after=epgc.after)
                self.errors[epgc.symbol] = err
                self.gen.set_gate_error(epgc.symbol, err.error_func,
                                        error_param=epgc.param)

    def configure_error_group(self, epgc, after):
        """configure an error group for a given epgc"""
        symbol_name = "{}_{}".format(epgc.symbol, "before")
        # ErrorSetMultiQuditGate
        err = self.error_set_from_epgc(epgc, after)
        self.errors[symbol_name] = err
        self.gen.set_group_error(epgc.symbol, err.error_func,
                                 error_param=epgc.param)

    def error_set_from_epgc(self, epgc, after):
        if any([hasattr(gate, "__iter__") for gate in epgc.error_gates]):
            return self.gen.ErrorSetMultiQuditGate(epgc.error_gates,
                                                   after=after)
        else:
            return self.gen.ErrorSet(epgc.error_gates, after=after)

    def generate_tick_errors(self, tick_circuit, time, **params):
        """Assign errors to a circuit as configured during initialization"""
        before = pecos.circuits.QuantumCircuit()
        after = pecos.circuits.QuantumCircuit()
        replace = set([])
        if isinstance(time, tuple):
            tick_index = time[-1]
        else:
            tick_index = time
        circuit = tick_circuit.circuit
        for symbol, gate_locations, _ in circuit.items(tick=tick_index):
            self.gen.create_errors(self, symbol, gate_locations, after,
                                   before, replace)
        self.error_circuits.add_circuits(time, before, after)
        idle_qudits = circuit.qudits - circuit.active_qudits[tick_index]
        # print("qudits:", circuit.qudits)
        # print("active qudits:", circuit.active_qudits[tick_index])
        # print("idle qudits:", idle_qudits)
        self.gen.create_errors(self, 'idle', idle_qudits, after,
                               before, replace)
        return self.error_circuits


class XErrorGen(GeneralErrorGen):
    """Generate X errors only on all types of gates"""
    @staticmethod
    def gen_error_prone_gates():
        return [ErrorProneGateCollection(symbol="init", ep_gates=_INITS_ALL,
                                         param="r",
                                         error_gates=_PAULI_X,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="one qubit",
                                         ep_gates=_ONE_QUBIT_GATES,
                                         param="p",
                                         error_gates=_PAULI_X,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="two qubit",
                                         ep_gates=_TWO_QUBIT_GATES,
                                         param="p",
                                         error_gates=_PAULI_X,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="measure",
                                         ep_gates=_MEASURE_ALL,
                                         param="s",
                                         error_gates=_PAULI_X,
                                         before=True, after=False),
                ]


class ZErrorGen(GeneralErrorGen):
    """Generate Z errors only on all types of gates"""
    @staticmethod
    def gen_error_prone_gates():
        return [ErrorProneGateCollection(symbol="init", ep_gates=_INITS_ALL,
                                         param="r",
                                         error_gates=_PAULI_Z,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="one qubit",
                                         ep_gates=_ONE_QUBIT_GATES,
                                         param="p",
                                         error_gates=_PAULI_Z,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="two qubit",
                                         ep_gates=_TWO_QUBIT_GATES,
                                         param="p",
                                         error_gates=_PAULI_Z,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="measure",
                                         ep_gates=_MEASURE_ALL,
                                         param="s",
                                         error_gates=_PAULI_Z,
                                         before=True, after=False),
                ]


class CodeCapacityGen(GeneralErrorGen):
    """Generate code capacity noise

    Generate errors on all one-qubit gates, inits and measurements
    with error parameters:
        -r: init       qubit initialization
        -p: one qubit  one qubit gates
        -s: measure    measurement
    """
    @staticmethod
    def gen_error_prone_gates():
        return [ErrorProneGateCollection(symbol="init", ep_gates=_INITS_ALL,
                                         param="r",
                                         error_gates=_PAULI_Z,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="one qubit",
                                         ep_gates=_ONE_QUBIT_GATES,
                                         param="p",
                                         error_gates=_PAULI_Z,
                                         before=False, after=True),
                ErrorProneGateCollection(symbol="measure",
                                         ep_gates=_MEASURE_ALL,
                                         param="s",
                                         error_gates=_PAULI_Z,
                                         before=True, after=False),
                IdleErrorCollection(symbol="idle", param="i",
                                    error_gates=_PAULI_ERRORS,
                                    before=False, after=True),
                ]
