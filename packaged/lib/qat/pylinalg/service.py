# -*- coding: utf-8 -*-
"""
@authors Bertrand Marchand
@brief pylinalg simulator service
@copyright 2017  Bull S.A.S.  -  All rights reserved.\n
           This is not Free or Open Source software.\n
           Please contact Bull SAS for details about its license.\n
           Bull - Rue Jean Jaurès - B.P. 68 - 78340 Les Clayes-sous-Bois
@namespace qat.pylinalg
"""
import numpy as np

import inspect

from qat.core.qpu import QPUHandler
import qat.core.simutil as core_simutil

from qat.comm.shared.ttypes import Sample, Result
from qat.comm.hardware.ttypes import HardwareSpecs
from qat.comm.exceptions.ttypes import RuntimeException, ErrorType
import qat.comm.datamodel.ttypes as datamodel_types
from qat.pylinalg import simulator as np_engine


class PyLinalg(QPUHandler):
    """
    Simple linalg simulator plugin.
    """
    def __init__(self):
        super(PyLinalg, self).__init__()
        self._circuit_key = None

    def submit_job(self, job):
        circ = job.circuit
        np_state_vec, _ = np_engine.simulate(circ) # perform simu
        if job.qubits is not None:
            meas_qubits = job.qubits
        else:
            meas_qubits = [k for k in range(circ.nbqbits)]
        all_qubits = False
        if len(meas_qubits) == circ.nbqbits:
            all_qubits = True

        result = Result()
        result.raw_data = []
        if job.type == 1:
            current_line_no = inspect.stack()[0][2]
            raise RuntimeException(code=ErrorType.INVALID_ARGS,
                                   modulename="qat.pylinalg",
                                   message="Unsupported sampling type",
                                   file=__file__,
                                   line=current_line_no)


        if job.type == 0: # Sampling
            if job.nbshots == 0: # Returning the full quantum state/proba distr
                if not all_qubits:
                    all_qb = range(circ.nbqbits) # shorter
                    sum_axes = tuple(qb for qb in all_qb if qb not in meas_qubits)

                    # state_vec is transformed into vector of PROBABILITIES
                    np_state_vec = np.abs(np_state_vec**2)
                    np_state_vec = np_state_vec.sum(axis=sum_axes)

                # setting up threshold NOT IMPLEMENTED! DUMMY VALUE!
                threshold = 1e-12

                # loop over states. val is amp if all_qubits else prob
                for int_state, val in enumerate(np_state_vec.ravel()):
                    amplitude = None # in case not all qubits
                    if all_qubits:
                        amplitude = datamodel_types.ComplexNumber()
                        amplitude.re = val.real
                        amplitude.im = val.imag
                        prob = np.abs(val)
                    else:
                        prob = val

                    if prob <= threshold:
                        continue

                    sample = Sample(int_state)
                    sample.amplitude = amplitude
                    sample.probability = prob

                    # append
                    result.raw_data.append(sample)
            else: ## Performing shots
                intprob_list = np_engine.measure(np_state_vec,
                                                 meas_qubits,
                                                 nb_samples=job.nbshots)

                # convert to good format and put in container.
                for res_int, prob in intprob_list:

                    amplitude = None # in case not all qubits
                    if all_qubits:
                        # accessing amplitude of result
                        indices = []
                        for k in range(len(meas_qubits)):
                            indices.append(res_int >> k & 1)
                        indices.reverse()

                        amplitude = datamodel_types.ComplexNumber()
                        amplitude.re = np_state_vec[tuple(indices)].real # access
                        amplitude.im = np_state_vec[tuple(indices)].imag # access

                    # final result object
                    sample = Sample(state=res_int,
                                    probability=prob,
                                    amplitude=amplitude)
                    # append
                    result.raw_data.append(sample)
            return result
        raise NotImplementedError

        return qproc_state_vec

get_qpu_server = PyLinalg
