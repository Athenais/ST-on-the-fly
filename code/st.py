#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division 

import math
import os
import pdb
import random
import re
import shlex
import shutil
import subprocess
import sys


import numpy as np
# scipy is a library (package) that contains modules 
# and to import a specific module from the scipy library, 
# it is needed to specify it and import the module itself.
# So do not : 
# >>> import scipy
# >>> scipy.constants.<etc>
# but : 
from scipy import constants


import logger
from md import MolecularDynamics


logger.set_functional_logger()
global log
log = logger.__logger


@logger.log_decorator
def create_simulation(simu_type, **kwargs): 
    """ Create a simulation of the chosen type

    Argumuents : 
    ------------
    simu_type : string
        Type of the simulation. 
        Could be : 
        'md' - Molecular Dynamics
        'mc' - Monte Carlo 
        Currently the only one that works is 'md'
    **kwargs :
        Every named argumnents needed for the constructor 
        of the chosen type.

    Return : 
    --------
    None if simu_type does not correspond to a rigth choice.
    -or-
    simulation : Simulation derived object
        Could be :  
        MolecularDynamicsProduction object 
        MonteCarlo object 
        Currently : can only return MolecularDynamicsProduction
    """
    if simu_type == 'md' : 
        return MolecularDynamicsProduction(**kwargs)
    elif simu_type == 'mc':
        return MonteCarlo(**kwargs)
    else : 
        logger.__logger.error('Wrong choice of simulation')
        return None

class Simulation(object):
    """Simulation class
    
    Correspond to the first step of ST experiment 

    Instance Attributs : 
    ---------------------
    T_current : int 
        Current temperature

    Must be overrided : 
    -------------------
    run method
    """
    @logger.log_decorator
    def __init__(self, T_current, **kwargs):
        print ('je suis dans le constructor de Simulation')

        super(Simulation,self).__init__(**kwargs)
        print ('je suis revenu de super')
        self._T_current = T_current

    @property
    def T_current(self):
        return self._T_current
    
    # XXX??? TODO : use abc. must be overrided

class MonteCarlo(Simulation):
    """MonteCarlo class 

    A possible kind of first step for ST experiment.
    Currently : not implemented

    Instance Attribut : 
    -------------------
    Those of simulation 

    """
    
    @logger.log_decorator
    def run(self):
        return compute_E_average()
    @logger.log_decorator
    def compute_E_average(self):
        return 0 # ??? XXX pass

class MolecularDynamicsProduction(Simulation,MolecularDynamics):
    """MolecularDynamicProduction class

    A possible kind of first step for ST experiment.
    Currently: working using GROMACS 

    Instance Attribut : 
    -------------------
    Those of Simulation 
    Those of MolecularDynamics
    """
    @logger.log_decorator
    def __init__(self, **kwargs):
        print ('je suis dans le constructor de Prod') 
        super(MolecularDynamicsProduction, self).__init__(**kwargs)
        self._mdp_template = kwargs['mdp_filename'] # ??? XXX A quoi il sert
        self._mdp_filename = '{0}_{1}.mdp'.format(self._mdp_template , self.T_current)


    @logger.log_decorator
    def run(self, tcurrent):
        save_out_name = self._out_name
        print (save_out_name)
        self._out_name += str(tcurrent)
        print (self._out_name)
        super(MolecularDynamicsProduction, self).run() # call MolecularDynamics.run()
        E = self.compute_E_average()
        os.rename("{0}/{1}.gro".format(self._out_path, self._out_name), self.gro_filename)
        self.cat_edr(tcurrent)
        self.cat_xtc(tcurrent)
        self._out_name = save_out_name
        return E


    def cat_gmx_files(self, fn, ext, t_current):
        
        
        if t_current == 0 : 
            cmd = 'gmx {0} -f {1}/{2}.{3} -o {1}/cat.{3}'.format(fn, self.out_path, self._out_name, ext)
            p = subprocess.Popen(shlex.split(cmd))
            p.wait()
        else : 
            cmd1 = "echo '0\n{0}\n'".format(t_current)
            p1 =  subprocess.Popen(cmd1, shell = True, stdout=subprocess.PIPE)

            cmd2 = ("gmx {0} -f {1}/cat.{3} {1}/{2}.{3} -o {1}/cat.{3}  -settime ".format(fn, self.out_path, self._out_name, ext))

            p2 = subprocess.Popen(shlex.split(cmd2), stdin=p1.stdout)
            p2.wait()
            p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        
       
    def cat_xtc(self, t_current):
        self.cat_gmx_files('trjcat', 'xtc', t_current)
        os.remove("{0}{1}.xtc".format(self.out_path, self._out_name))

    def cat_edr(self, t_current):
        self.cat_gmx_files('eneconv', 'edr', t_current)
        os.remove("{0}{1}.edr".format(self.out_path, self._out_name))


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
                return -int(E_average) 
                # in NGuyen 2013, Energies are defined as integral -> positive
                # in gmx, E are negative -> take the oposite to have positive value
        log.error('E_average could not be found') 
        

    @Simulation.T_current.setter
    def T_current(self, T_new):
        
        print ("setter de Tcurrent ============")
        self.update_velocities(T_new)

        self._T_current = T_new 
        # not self.T_current = T_new
        # otherwise it calls the setter that calls the setter, that c... 
        # do not use setter in setter ! 
        
        self._mdp_filename = self._mdp_template % self.T_current

        
        

    def update_velocities(self, T_new):

        #Can't change a file, so create a new temp one...
        nb_of_atom = 0 

        with open(self.gro_filename, 'r') as infile, \
            open(self.gro_filename+'.tmp', 'w') as outfile    :
            for line_idx, line in enumerate (infile) : 

                # gro file line : 
                #"%5d%-5s%5s%5d%8.3f%8.3f%8.3f%8.4f%8.4f%8.4f" + \n
                # |___________44_____________|              |
                # |____________________68___________________|

                # nb of atom on seconde line -> 2-1
                if line_idx == 1 : 
                    nb_of_atom = int(line )

                # from third line to x = 3 + nb_of_atom th line : 
                if line_idx in xrange(2, 2 + nb_of_atom ) : 
                	# this range do not take the line defining the box

                    if len(line) < 69: # 68 + \n 
                        log.error('There is no velocities in the {0} file'.format(infile))
                        exit(-1)

                    velocities = [ float(line[44:52]), float(line[52:60]), float(line[60 :68 ]) ]
                    new_velocities = list()
                    for velocity in velocities : 
                        new_velocity = velocity * math.sqrt(T_new / self.T_current)
                        new_velocities.append(new_velocity)
                    
                    line = "{0}{1:8.4f}{2:8.4f}{3:8.4f}\n".format(line [:44], *new_velocities)
                    

                outfile.write(line)
        # ... and rename it (the old one is erase)
        os.rename(self.gro_filename+'.tmp', self.gro_filename)






class SimulatedTempering(object):
    """SimulatedTempering class
    
    Nested classes : 
    ----------------
    TRange
    Temperature 

    

    """

    class TRange(list):
        """ TRange class 

        A list-like without negative indiciation

        Specific Exception : 
        --------------------
        NegativeIndexError 

        Attributes : 
        -----------
        Those of list
        """

        class NegativeIndexError(IndexError):
            """NegativeIndexError Exeption

            Atributes : 
            ------------
            Those of IndexError
            """
            def __init__(self,*args,**kwargs):
                super(Exception, self).__init__(*args,**kwargs)


        def __getitem__(self, idx):
            """Get item corresponding to the given index

            Override list getitem to disable negative indices

            Argument : 
            ----------
            idx : int positive 
                index of the wanted element 
                0 <= idx <= len (list)

            Return : 
            --------
            wanted element 

            Raise : 
            -------
            NegativeIndexError : 
                if idx < 0 
            IndexError : 
                if idx > len (list)
            TypeError : 
                if idx not int 
            """
            if isinstance(idx, int):
                if idx < 0:
                    
                    raise SimulatedTempering.TRange.NegativeIndexError ("neg index not allowed")
                    
                else :  
                    return super(SimulatedTempering.TRange, self).__getitem__(idx)
            else : 
                raise TypeError ("TRange indices must be integers, not "+ str(type (idx) ) )  




    class Temperature(object):
        """Temperature class

        Specific Exeption : 
        -------------------
        NoECurrent 

        Class attribute: 
        ----------------
        k_Boltzmann : float 
            Boltzmann constant in kJ / K (same unit than Gromacs)

        Instance attributes : 
        ---------------------
        VALUE : float, constant
            The temperature itself in Kelvin (same unit than Gromacs)
        number_of_passes : int
            The number of time ST used this temperature
        f : float
            The weight associated to this temperature 
        E : float / None
            The average potential energy for this temperature 
        BETA : float, constant 
            the beta constant for this temperature
            = 1 / (k_Boltzmann * VALUE)
        """

        class NoECurrent(Exception):
            """NoECurrentExeption

            Raised when trying to use E that is None 
            """
            def __init__(self):
                super(SimulatedTempering.Temperature.NoECurrent, self).__init__()


        k_Boltzmann = constants.value(u'Boltzmann constant') / 1000 
        # using gromacs, E are in kilo Joule / K 
        # scipy gives Boltmann constant in Joule per K -> / 1000 

        def __init__(self, value):
            """ Temperature constructor

            Argument : 
            ----------
            value : float 
                The value of the temperature
            """
            super(SimulatedTempering.Temperature, self).__init__()
            self._VALUE = value
            self._number_of_passes = 0 
            self._f = 0
            self._E = None
            self._BETA  = self.compute_beta()


        @logger.log_decorator
        def compute_beta(self):
            """Compute the beta constant of the temperature

            Return : 
            --------
            beta : float 
                beta constant of the Temperature 
            """
            return 1/ (SimulatedTempering.Temperature.k_Boltzmann * self._VALUE)
            # __future__ division -> floting point division


        @logger.log_decorator
        def update_f(self, Tprev) : 
            """Update the weight of the Temperature 

            The update is done with either a computation 
            or with an estimation if the computation is impossible.
            """
            try:
                self.compute_f(Tprev)
            except SimulatedTempering.Temperature.NoECurrent:
                self.estimate_f(Tprev)


        @logger.log_decorator
        def estimate_f(self, Tprev):
            """Do an estimation of the weight of the temperature

            Use the formula in Nguyen 2013 : 
            (beta_next - beta_previous) E_previous / 2
            """

            self._f = (self._BETA - Tprev._BETA ) * Tprev._E / 2


        @property
        def E(self):
            """E getter

            Return : 
            --------
            E : float 
                The average potential energy for this temperature 

            Raise :
            -------
            NoECurrent : 
                if E is None

            """
            if not self._E : 
                raise SimulatedTempering.Temperature.NoECurrent
            else : 
                return self._E
        
        @logger.log_decorator
        def compute_f(self, Tprev):
            """Do a computation of the weight of the temperature 

            Use the formula in Nguyen2013 
            f_prev + (beta_curr - beta_prev) (E_curr + E_prev) / 2 

            Raise : 
            -------
            NoECurrent : 
                If E_Tcur is not available
            """
            try:
                self._f =  Tprev._f + (self._BETA - Tprev._BETA ) * ( self.E + Tprev.E )  / 2
            except SimulatedTempering.Temperature.NoECurrent:
                if not self.E : 
                    print ('no E for T = {}'.format(self._VALUE))
                    raise 
                elif not Tprev.E : 
                    print ('problem when trying to access E for T = {}'.format(self._VALUE))
                    exit()


        @logger.log_decorator
        def update_E(self, E_new):
            """Update E including E_new in E

            Parameter : 
            ------------
            E_new : float 
                The average potential energy for the last MD runed with this temperature 
                to be included in E.

            """
            self._number_of_passes += 1 
            try:
                self._E =  self.E  + ( (E_new - self.E ) / self._number_of_passes)
            except SimulatedTempering.Temperature.NoECurrent: 
                #self._E = None becase no updated yet
                #First time init : 
                self._E =  ( E_new  / self._number_of_passes)
            
    @logger.log_decorator
    def __init__(self, num_simu, Tmin, Tmax, Tnum, simu_type='md', st_mdp_template_filename = None, **kwargs):
        
        super(SimulatedTempering,self).__init__()
        self._NUM_SIMU = num_simu
        self._T_RANGE=SimulatedTempering.TRange() 
        self._ST_MDP_TEMPLATE_FILENAME= st_mdp_template_filename
        self.md_step = SimulatedTempering.get_md_step(st_mdp_template_filename)
        T_range = np.logspace(np.log10(Tmin), np.log10(Tmax), num=Tnum, endpoint=True)
        for T in T_range:
            if simu_type == 'md' : 
                self.create_mdp(T)
            self._T_RANGE.append(SimulatedTempering.Temperature(T))
        for T in self._T_RANGE : 
            print (T._VALUE, T._BETA)
        #range (a, b) = [a, b[
        #range (a, b+1) = [a, b+1[ = [a, b]
        kwargs['T_current'] = self._T_RANGE[0]._VALUE
        kwargs['mdp_filename'] = self._ST_MDP_TEMPLATE_FILENAME
        self._SIMULATION=create_simulation(simu_type, **kwargs ) #pattern strategy

    @staticmethod
    @logger.log_decorator
    def get_md_step(st_mdp_template_filename):
        with open(st_mdp_template_filename, 'r') as fin: 
            for line in fin : 
                if line.startswith("dt") : 
                    dt= float(re.split(r'[=;]', line)[1])
                elif line.startswith("nsteps") : 
                    nsteps = float(re.split(r'[=;]', line)[1])
        return dt * nsteps

    @logger.log_decorator
    def create_mdp(self, T) : 
        
        mdp_filename = '{0}_{1}.mdp'.format(self._ST_MDP_TEMPLATE_FILENAME, T)

        with open(self._ST_MDP_TEMPLATE_FILENAME, 'r') as infile, \
            open(mdp_filename, 'w') as outfile    :
            for line in infile : 
                if line.startswith('ref_t') : 
                    line = "ref_t = {0}\n".format(T)

                outfile.write(line)


    @property
    def T_current(self):
        return self._T_RANGE[self.T_current_idx]
    
    @property    
    def T_current_idx(self):
        return self.get_T_idx(self._SIMULATION.T_current)

    def get_T_idx(self, T_wanted) : 
        return [T._VALUE for T in self._T_RANGE].index(T_wanted)
        
    @logger.log_decorator
    def update_f_current(self):
        try : 
            T_previous = self._T_RANGE[self.T_current_idx-1]
            self.T_current.update_f(T_previous)
        except SimulatedTempering.TRange.NegativeIndexError : #no previous T because Tcurrent = Tmin 
            self.T_current._f = 0 #f_Tmin is always equal to 0.

        # Remember : 
        # If an exeption occurs during execution of the try clause,
        # the rest of the clause is skipped.    

    @logger.log_decorator
    def update_f_next(self):
        try : 
            T_next = self._T_RANGE[self.T_current_idx + 1 ]
            T_next.update_f( self.T_current)
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
        try:
            direction= SimulatedTempering.toss_coin()
            print ('direction = '+str(direction))
            
            T_attempt = self._T_RANGE[self.T_current_idx + direction ]
        except IndexError:
            T_attempt = None
        return T_attempt

    @logger.log_decorator
    def compute_metropolis_criterion(self, T_attempt) : 

        try:
            insider = - (                                                        \
                ( T_attempt._BETA- self.T_current._BETA )  * self.T_current._E   \
                - ( T_attempt._f - self.T_current._f )                           \
            )           
            res = math.exp ( insider  ) 
        except OverflowError: 
            if insider < 0 : 
                res = 0
            elif insider > 0 : 
                res = float('inf')
            else : 
                print ('case not handled !! ')
        
        mc = min (1, res)
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
    def write_results (self, idx, t_current, E_current_average) : 
        with open('./st.results', 'a') as fout: 
            to_write = "{0}\t{1}\t{2}\t{3}\t{4}".format(
                idx, 
                t_current,
                self.T_current._VALUE, 
                E_current_average, 
                self.T_current._E)
            for T in self._T_RANGE : 
                to_write += "\t{0}".format(T._f)
            to_write += '\n'
            fout.write (to_write )


    @logger.log_decorator
    def run(self):
        for step_idx in xrange(self._NUM_SIMU) : 
            t_current = step_idx * self.md_step

            E_current_average = self._SIMULATION.run(t_current)

            self.T_current.update_E(E_current_average) 

            self.update_f_current()
            self.update_f_next ()

            self.write_results(step_idx, t_current, E_current_average)

            T_attempt = self.choose_T_attempt()
        
            if self.attempt_OK(T_attempt) : 
                self._SIMULATION.T_current = T_attempt._VALUE #if MD : change velocity --> Overriding
            else : 
                self._SIMULATION.T_current = self.T_current._VALUE #if MD : change velocity --> Overriding


