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
GateError = collections.namedtuple("GateError", ("error_param", "after"))

ErrorProneGateCollection = collections.namedtuple("ErrorProneGateCollection",
                                                  ("symbol", "ep_gates",
                                                   "param", "error_gates",
                                                   "before", "after"))
IdleErrorCollection = collections.namedtuple("IdleErrorCollection",
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
                symbol="measure_z",
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
        self.epgc_list = None
        super().__init__()  # ParentErrorGen takes no args/kwargs
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
        return str(self.epgc_list)


class GeneralErrorGen(__BaseErrorGen):
    """Highly configurable error generator with a user friendly interface"""

    ALLOWED_EPGC_TYPES = (ErrorProneGateCollection, IdleErrorCollection)

    def configure_error_generator(self, epgc_list=list()):
        """Configure the error generator

        The kwargs defined above should be passed at init time, or by
        calling this method after init time with the proper parameters

        Args:
            epgc_list, list of ErrorProneGateCollection or IdleErrorCollection
                tracks which gates are error prone / if idle locations can
                have errors.
        """
        self.epgc_list = epgc_list
        self.excluded_qudits = None
        self.configure_generator_from_epgc_list(self.epgc_list)

    def reconfigure(self):
        """High level method to reconfigure the error generator.

        The intended use is to update the epgc_list directly and then call
        the reconfigure class like the example below:
            >>> MyGenerator = GeneralErrorGen()
            >>> MyGenerator.epgc_list.append(an_epgc_object)
            >>> MyGenerator.reconfigure()
        """
        self.configure_generator_from_epgc_list(
                self.epgc_list, clear_generator=True)

    def configure_generator_from_epgc_list(self, epgc_list,
                                           clear_generator=False):
        """Handle error_gen init from ErrorProneGateCollection objects

        This method implements the automatic initialization of all objects
        in the epgc_list list, which should ocntain exclusively
        ErrorProneGateCollection (epgc) objects or by exception for
        idle errors which do not specify gates to operate on but act only
        on idle qubits IdleErrorCollection (iec).

        the configure_generator_from_epgc_list method may also take a new list
        of error prone gates. If clear_generator is set to True, the error
        generator is fully reset, basically fully changing the way errors
        are generated to the new list of supplied epgc_list.

        Args:
            epgc_list, list of ErrorProneGateCollection objects
            clear_generator, bool to fully reset the generator object
        """
        types = self.ALLOWED_EPGC_TYPES
        if not isinstance(epgc_list, list):
            raise TypeError(f"epgc_list should be of type list but is of type"
                            f" {type(epgc_list).__name__}")
        if not all([isinstance(epgc, types) for epgc in epgc_list]):
            types = set([type(x).__name__ for x in epgc_list])
            raise TypeError("epgc_list should be list of "
                            "ErrorProneGateCollection or IldeErrorCollection"
                            f" objects but contains the types: {types}")

        if clear_generator:
            self.gen = self.generator_class()

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

    def filter_excluded(self, locations, excluded):
        filtered_locations = set()
        for loc in locations:
            if isinstance(loc, tuple):
                # filter multi qudit locations
                if not any(sub_loc in excluded for sub_loc in loc):
                    filtered_locations.add(loc)
            elif isinstance(loc, int):
                # filter single qudit locations
                if loc not in excluded:
                    filtered_locations.add(loc)
            else:
                raise NotImplementedError("filter excluded cannot handle"
                                          f"location of type {type(loc)}")
        return filtered_locations

    def generate_tick_errors(self, tick_circuit, time, **params):
        """Assign errors to a circuit as configured during initialization"""
        if "excluded_qudits" in params.keys():
            self.excluded_qudits = params["excluded_qudits"]

        before = pecos.circuits.QuantumCircuit()
        after = pecos.circuits.QuantumCircuit()
        replace = set([])
        if isinstance(time, tuple):
            tick_index = time[-1]
        else:
            tick_index = time
        circuit = tick_circuit.circuit
        for symbol, gate_locations, _ in circuit.items(tick=tick_index):
            if self.excluded_qudits is not None:
                gate_locations = self.filter_excluded(gate_locations,
                                                      self.excluded_qudits)
            print(gate_locations)
            self.gen.create_errors(self, symbol, gate_locations, after,
                                   before, replace)

        # add idle errors
        idle_qudits = circuit.qudits - circuit.active_qudits[tick_index]
        if self.excluded_qudits is not None:
            gate_locations = self.filter_excluded(idle_qudits,
                                                  self.excluded_qudits)
        else:
            gate_locations = idle_qudits
        self.gen.create_errors(self, 'idle', gate_locations, after,
                               before, replace)

        # add faults to circuit
        self.error_circuits.add_circuits(time, before, after)
        return self.error_circuits
