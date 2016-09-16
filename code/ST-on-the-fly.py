#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Run ST-on-the-fly"""



from __future__ import print_function
from __future__ import division 

import logger


import subprocess
import shlex

import random


import scipy

import math

import numpy as np

class ListWithoutNegIdx(list):

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0:
                raise IndexError("negative index not allowed")
            else :  
                return super(ListWithoutNegIdx, self).__getitem__(key)
        else : 
            raise TypeError ("ListWithoutNegIdx indices must be integers, not "+ str(type (key) ) )  




class MolecularDynamics(object):
    """docstring for MolecularDynamics"""
    @logger.log_decorator
    def __init__(self, mdp_filename, gro_filename, top_filename, out_path, out_name, maxwarn, **kwargs):
        print ('je suis dans le constructor de MolecularDynamics')
        super(MolecularDynamics, self).__init__(**kwargs)
        self._mdp_filename = mdp_filename
        self._gro_filename = gro_filename
        self._top_filename = top_filename
        self._out_path = out_path
        self._out_name = out_name
        self._maxwarn = maxwarn

    @property 
    def mdp_filename(self):
        return self._mdp_filename
    @property 
    def gro_filename(self):
        return self._gro_filename
    @property 
    def top_filename(self):
        return self._top_filename
    @property 
    def out_path(self):
        return self._out_path
    @property 
    def out_name(self):
        return self._out_name
    @property 
    def maxwarn(self):
        return self._maxwarn

    @logger.log_decorator
    def run(self):
        print ('MD.run()=========')

    @logger.log_decorator
    def gmx_grompp(self) : 
        cmd = "gmx grompp -f {0} -c {1} -p {2} -o {3}.tpr -po {3}.mdp -maxwarn {4}".format(   \
            self.mdp_filename, \
            self.gro_filename, \
            self.top_filename, \
            self.out_path + self.out_name , \
            self.maxwarn \
        )
        print (cmd)
        p = subprocess.Popen(shlex.split(cmd))
        p.wait()

    @logger.log_decorator
    def gmx_mdrun(self):
        cmd = "gmx mdrun -v -s {0}.tpr -o {0}.trr -e {0}.edr -g {0}.log -c {0}.gro".format(self.out_path + self.out_name)
        print (cmd)
        p = subprocess.Popen(shlex.split(cmd))
        p.wait()

    @logger.log_decorator
    def run(self): 
        self.gmx_grompp()
        self.gmx_mdrun()

class Simulation(object):
    """docstring for Simulation"""
    @logger.log_decorator
    def __init__(self, T_current, **kwargs):
        print ('je suis dans le constructor de Simulation')

        super(Simulation,self).__init__(**kwargs)
        print ('je suis revenu de super')
        self.T_current = T_current


class MonteCarlo(Simulation):
    """docstring for MonteCarlo"""
    
    @logger.log_decorator
    def run(self):
        return compute_E_average()
    @logger.log_decorator
    def compute_E_average(self):
        return 0

class MolecularDynamicsProduction(Simulation,MolecularDynamics):
    """docstring for MolecularDynamicProduction"""
    @logger.log_decorator
    def __init__(self, **kwargs):
        print ('je suis dans le constructor de Prod') 
        super(MolecularDynamicsProduction, self).__init__(**kwargs)
        self._mdp_template = kwargs['mdp_filename']
        self._mdp_filename = self._mdp_template % self.T_current


    @logger.log_decorator
    def run(self):
        super(MolecularDynamicsProduction, self).run() # call MolecularDynamics.run()
        return self.compute_E_average()

    @logger.log_decorator
    def gmx_energy(self, arg = 'Potential') : 

        p1 = subprocess.Popen( shlex.split("echo {0}".format(arg)), stdout=subprocess.PIPE ) 

        cmd = "gmx energy -f {0}.edr -o {0}_Potential.xvg ".format(
                    self.out_path + self.out_name
                )
               
        p2 = subprocess.Popen(shlex.split(cmd), stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        p2_com = p2.communicate() 
        p2_out = p2_com[0].split('\n') 

        return p2_out

    @logger.log_decorator
    def compute_E_average(self):
        output = self.gmx_energy('Potential')
        for line in output : 
            splitted_line = line.split()
            print (splitted_line)
            if splitted_line and splitted_line[0] == 'Potential' : 
                E_average = splitted_line[1]
                return E_average
        logger.__logger.error('E_average could not be found') 
        return 0

    @property.setter
    def T_current(self, T_new):
        self._T_current = T_new

    
@logger.log_decorator
def create_simulation(simu_type, **kwargs): 
    if simu_type == 'md' : 
        return MolecularDynamicsProduction(**kwargs)
    elif simu_type == 'mc':
        return MonteCarlo(**kwargs)
    else : 
        logger.__logger.error('Wrong choice of simulation')
        return None


class Temperature(object):
    """docstring for Temperature"""

    k_Boltzmann = scipy.constants.value(u'Boltzmann') # ??? k

    def __init__(self, value):
        super(Temperature, self).__init__()
        self._VALUE = value
        self._number_of_passes = 0 
        self._f = 0
        self._E = None
        self._BETA  = self.compute_beta()

    
    # @classmethod returns descriptor objects, not functions. 
    # problem : most decorators are not designed to accept descriptors.
    # solution : @classmethod must be the top-most decorator 
    # for another decorator to decorate it.
    @classmethod
    @logger.log_decorator
    def compute_beta(self):
        return 1/cls.k_Boltzmann * self._VALUE
        # __future__ division -> floting point division


    @logger.log_decorator
    def update_f(self, Tprev) : 
        try:
            self.compute_f(Tprev)
        except NoECurrent:
            self.estimate_f(Tprev)


    @logger.log_decorator
    def estimate_f(self, Tprev):
        # (beta_next - beta_previous) E_previous / 2
        self._f = (self._BETA - Tprev._BETA ) * Tprev._E / 2


    @logger.log_decorator
    def compute_f(self, Tprev):
        # f_prev + (beta_curr - beta_prev) (E_curr + E_prev) / 2 
        self._f =  Tprev._f + (self._BETA - T_previous._BETA ) * ( self._E + T_previous._E )  / 2


    @logger.log_decorator
    def update_E(self, E_new):

        self._E =  self._E  + ( (E_new - self._E ) / self._number_of_passes)
        


class SimulatedTempering(object):
    """docstring for ST"""

    @logger.log_decorator
    def __init__(self, num_step, Tmin, Tmax, Tstep, simu_type='md', **kwargs):
        
        super(SimulatedTempering,self).__init__()
        self._NUM_STEP = num_step
        self._T_RANGE=ListWithoutNegIdx() 
        for T in  xrange(Tmin, Tmax+1, Tstep) : 
            self._T_RANGE.append(Temperature(T))
        #range (a, b) = [a, b[
        #range (a, b+1) = [a, b+1[ = [a, b]
        kwargs['T_current'] = Tmin
        self._SIMULATION=create_simulation(simu_type, **kwargs ) #pattern strategy

        self._step_idx=0
        self._measure_sequence=[]

    @property
    def T_current(self):
        return self._T_RANGE[self.T_current_idx]
    
    @property    
    def T_current_idx():
        return self.get_T_idx(self._SIMULATION.T_current)

    def get_T_idx(self, T_wanted) : 
        return [T._VALUE for T in self._T_RANGE].index(T_wanted)
        
    @logger.log_decorator
    def update_f_current(self):
        i_current = self.T_current_idx()
        try : 
            T_previous = self._T_RANGE[i_current-1]
            self._SIMULATION.T_current.update_f(T_previous)
        except IndexError : #no previous T because Tcurrent = Tmin 
            self._f[T] = 0 #f_Tmin is always equal to 0.

        # Remember : 
        # If an exeption occurs during execution of the try clause,
        # the rest of the clause is skipped.    

    @logger.log_decorator
    def update_f_next(self):
        i_current = self.T_current_idx()
        try : 
            T_next = self._T_RANGE[i_current + 1 ]
            T_next.update_f( self._SIMULATION.T_current )
        except IndexError : #no next T because Tcurrent = Tmax 
            pass

        # Remember : 
        # If an exeption occurs during execution of the try clause,
        # the rest of the clause is skipped.    



    # @staticmethod returns descriptor objects, not functions. 
    # problem : most decorators are not designed to accept descriptors.
    # solution : @staticmethod must be the top-most decorator 
    # for another decorator to decorate it.
    @staticmethod
    @logger.log_decorator
    def toss_coin():
        return random.choice ( [-1, 1] )


    @logger.log_decorator
    def choose_T_attempt(self):
        i_current =self.T_current_idx()
        try:
            T_attempt = self._T_RANGE[i_current + SimulatedTempering.toss_coin() ]
        except IndexError:
            T_attempt = None
        return T_attempt

    @logger.log_decorator
    def compute_metropolis_criterion(self, T_attempt) : 

        try:
            f_attempt = self.f[T_attempt]
        except KeyError:
            f_attempt = self.f_attempt_estimate(T_attempt)

        mc = min 
            (
                1, 
                math.exp(
                            - (
                                  (
                                      self._BETA[T_attempt] - self._BETA[self.simulation.T_current]
                                  ) * self.simulation.E_average #self._measure_sequence[-1][1]
                                - (
                                    f_attempt - self.f[self.simulation.T_current]
                                  )
                              )
                        )
            )
        return mc
        # mc = min (1 , exp (-   [  (beta_attempt - beta_current) * E_current_average  -   (f_attempt_estimate - f_current_compute)  ]   ) )

    @logger.log_decorator
    def attempt_OK(self, T_attempt):
        if not T_attempt : return False
        mc =  self.compute_metropolis_criterion(T_attempt) 
        if mc == 1 : 
            return True
        else : 
            return False

    @logger.log_decorator
    def run(self):
        while self.step_idx < self.MAX_NUM_STEP : 

            E_current_average = self.simulation.run()

            self.T_current.update_E(E_current_average) 

            self.update_f_current()
            self.update_f_next ()

            self._measure_sequence.append( (self.simulation.T_current, E_current_average) )

            T_attempt = self.choose_T_attempt()
        
            if self.attempt_OK(T_attempt) : 
                self.simulation.T_current = T_attempt #if MD : change velocity --> Overriding

if __name__ == "__main__":
    print ('go')
    logger.set_functional_logger()

    logger.__logger.info('logger OK')

    logger.__logger.info('get args')

    num_step = 100
    dt_pas = 1
    dt_attempt = 10 
    Tmin = 1 
    Tmax = 10 
    Tstep = 1 

    logger.__logger.info('run minimi')
    MD_minimi = MolecularDynamics(        
        mdp_filename = '../data/mini2.mdp', 
        gro_filename = '../data/ala10_md000.pdb', 
        top_filename = '../data/ala10.top', 
        out_path = './', 
        out_name = 'minimisation_before_ST', 
        maxwarn = 13)
    MD_minimi.run()
    logger.__logger.info('minimi OK')

    logger.__logger.info('new ST')
    ST = SimulatedTempering(
        num_step, 
        Tmin, Tmax, Tstep, 
        'md',  
        mdp_filename = '../data/md1.mdp', 
        gro_filename = './minimisation_before_ST.gro', 
        top_filename = '../data/ala10.top', 
        out_path = './', 
        out_name = 'ST-simu', 
        maxwarn = 13
    )
    
    logger.__logger.info('ST.run')


    logger.__logger.info('the end')