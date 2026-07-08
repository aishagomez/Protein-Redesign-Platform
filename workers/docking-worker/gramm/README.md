# GRAMM 

This repository includes the source code for GRAMM, along with instructions on how to build and execute it locally. 


**GRAMM** (**G**lobal **RA**nge **M**olecular **M**atching) is a protein-protein docking software that systematically maps the intermolecular energy landscape by predicting a spectrum of docking poses. The procedure calculates the docking score, correlated with van der Waals energy of interaction, in different orientations corresponding to stable (deep energy minima) and transient (shallow minima) protein interactions.

GRAMM is accessible through a user-friendly web application at https://gramm.compbio.ku.edu/ 

GRAMM should be cited as:

Webserver and current version: [Singh, A., Copeland, M.M., Kundrotas, P.J., Vakser, I.A., 2024, GRAMM Web Server for Protein Docking, Methods in Mol. Biol., 2714:101-112](https://doi.org/10.1007/978-1-0716-3441-7_5).

First published method: [Katchalski-Katzir, E., Shariv, I., Eisenstein, M., Friesem, A.A., Aflalo, C., Vakser, I.A., 1992, Molecular surface recognition: Determination of geometric fit between proteins and their ligands by correlation techniques, Proc. Natl. Acad. Sci. USA, 89:2195-2199.](https://doi.org/10.1073/pnas.89.6.2195).



## Build Instructions

### Linux
You'll need the following tools and libraries installed to build gramm on your system.

* fftw3
* openmpi (libraries and compilers for C and Fortran)
* gfortran
* gcc

Once you have these installed, you should be able to run the command **build** within the gramm directory to produce the **gramm** executable.


### MacOS (ARM64)

You'll need openmpi installed via brew with the command:
````
brew install open-mpi
````

You will also need to install fftw3 not from brew, but via the source.  You'll want to use the following options, once fftw is downloaded and unpacked in the fftw source directory.
````
./configure --enable-mpi --enable-single  --enable-threads
make -j 10
sudo make install
````

Once this is complete, you should be able run the command **build** within the gramm source directory to produce the **gramm** executable.


## User instructions

**GRAMM** performs an exhaustive 6-dimensional search through the relative translations and rotations of the molecules using the standard FFT (Fast Fourier Transform) algorithm. The input structure files for the two proteins involved in the interaction, generally referred to as the '**receptor**' and '**ligand**', should be in standard PDB format and include ATOM records. The standard docking parameters are specified in various parameter files with the extension ***.gr**. 

### Input parameter files:

- **rmol.gr** lists input 'receptor' and 'ligand' proteins to be docked. Users can input multiple molecular pairs in a row, as shown in the example below. Comment out a line by placing # as the first character.
```
      # Filename  Fragment  ID      Filename  Fragment  ID     [paral/anti  max.ang]
      # ----------------------------------------------------------------------------
      
        2vyc1.pdb    *    2vyc1    2vyc2.pdb     *     2vyc2
        2ptcE.pdb    *    2ptcE    2ptcI.pdb     *     2ptcI
        2ptc.pdb     E    2ptcE     2ptc.pdb     I     2ptcI
        2hhb.pdb   1-106  2hhbA     2hhb.pdb     B     2hhbB
      # 3apr.pdb     E    3aprE     3apr.pdb     I     3aprI
```
The first molecule is considered as 'receptor' and the second as 'ligand'. Filename is the input structure file in PDB format and Fragment can be defined as:
   `
      * - whole structure ;
      X - select specific chain (case sensitive) ;
      xx-xx - atom numbers (first-last).
   `
ID is any string of characters (no spaces in between) to identify molecules that is used to name GRAMM output file(s). 



- **rpar.gr** lists standard docking parameters to perform the scan stage. All parameters have optimal values.
```
Matching mode (docking/helix/overlap) ......................... mmode= docking
Grid step ....................................................... eta= 3.5
Repulsion (attraction is always -1) .............................. ro= 9
Attraction double range (fraction of single range) ............... fr= 0.0
Potential range type (atom_radius, grid_step) ................. crang= grid_step
Projection (blackwhite, gray) .................................. ccti= gray
Representation (all, hydrophobic, c-alpha) ..................... crep= all
Number of matches to output .................................... maxm= 30000
Angle,deg(5,6,7,8,9,10,12,15,18,20,30,40,50,60,70,80,90,0-no rot.) ai= 10
```



- **wlist.gr** lists *.res files (output of scan), GRAMM generated output file names in a combination of receptor and lingad IDs from `rmol.gr`.
```
# File_of_scan_predictions

  2vyc1-2vyc2.res
  2ptcE-2ptcI.res
  2hhbA-2hhbB.res
#  3aprE-3aprI.res
```



- **wpar.gr** is for the refine procedure which generates protein-protein complex PDB files for predicted doceking poses in *.res file. 
```
Number of scan matches to input .............................. mtch_l= 20000
Scoring vdw  (0-no, 1-rglr, 2-implicit s/chains) ............. scovdw= 0
Scoring stat (0-no, 1-GSVB, 2-MJ) ............................ scosta= 0
Constraints  (0-no, 1-yes) ...................................    ctr= 0
Cluster RMSD radius (0-no cluster) ........................... rclusl= 10
Backtrack (0-no, 1-rigid, 2-flexible implicit) ...............   mbak= 0
Number of matches to output (max no of refinement processes)   maxmch= 100
Output file separate/joint ..................................... sejo= joint
```


- **rcon.gr** lists any interacting residues of one or both proteins, i.e., the search space is constrained by the a priori information on interacting residues. 
```

# Protein_name  No_of_residues_in_constraints
# Res_number    Confidence_(0-10)

2hhbA  3
3     10
10    10
101   10

2hhbB  2
10     9
13     8

2ptcE  4
3      2
5      1
11    10
203    5
```
This file provides an option to filter/rescore the docking poses based on a list of interacting residues of one or both proteins. In addition to residue numbers, a confidence score ranging from 0 to 10 (where a higher score indicates a higher reliability of the constraint) should also be provided next to each residue number, separated by a space.



- **rusr.gr** is optional and provides access to some more intricate functions, such as choosing the grid size, initial rotation of the input structure, different output options for docked structure coordinates, models of CAPRI criteria (defined in `rcr3.gr`), etc.



### Execute gramm

#### Free docking:

Unpack `ang` files and put them in a separate directory. Define that directory in `GRAMMDAT` environmental variable. 
```
export GRAMMDAT=/path/to/GRAMM/ANG/
```

GRAMM first performs a global scan search, producing .res files for each complex. These files are then processed by the 'refine' procedure, which generates PDB files that can be joint or separate, as detailed in the wpar.gr file.
````
./gramm scan
./gramm refine 
````
Or both steps can be executed in one run:
````
./gramm scan refine
````
It creates a `gramm.log` file in the working directory, where any errors or run completion messages will be stored. The docking scores and the transformation matrix (rotation angles and translation vectors for the generation of the docking poses from the initial coordinates) of each docked pair are stored in the `receptorID-ligandID.res` file. Do not modify the `.res` file, it has to be in the exact format for the building of PDB structures of the predicted complexes. The final docked models are stored as a protein–protein complex in PDB format, where the REMARK section contains information about docked structures and chain assignment.

GRAMM uses a rigid-body docking approach, which means that it assumes that protein structures are rigid and do not undergo significant conformational changes upon binding. It performs an exhaustive 6-dimensional search and provides configurations of the complex with higher shape complementarity. The quality of the prediction relies on the accuracy of the structures. To account for this, GRAMM offers an option to adjust the docking resolution, allowing a grid step in `rpar.gr` between 1.5 to 7 Å. In cases involving significant conformational changes, where only the main structural features are known, low-resolution docking is preferable to identify potential regions of the global minimum (see referece section for deatiled studies).



#### Template based docking:

In addition to free docking, GRAMM also offers template-based docking (TBD). The TBD is performed by aligning the structure of the target proteins with either the full structure or the interface-only structure of the templates. Thus, TBD would require structures of the temples, either the full structure or the interface-only structure. These structural templates are available in our Dockground resources: https://dockground.compbio.ku.edu/bound/templates.php.

To utilize TBD, you should provide the path to the templates defined in the `GRAMMTEMPLATES` environmental variable. 
```
export GRAMMTEMPLATES=/path/to/templates/
```
In this directory, store full strucutre templates in a subdirectory named `full` and interface-only structures in a subdirectory named `intr`. Each subdirectory must contain a file named `list` that includes the names of the templates. The structures of individual chains from the templates should be saved separately with the extensions `*_1.pdb` and `*_2.pdb`.

The docking parameters for TBD are difined in parameter file `tpar.gr`
````
Alignment (full, intr) ........................................ amode= full
TM-score for A (0.0 - 1.0) ................................... tmscoa= 0.4
TM-score for B (0.0 - 1.0) ................................... tmscob= 0.4
Coverage for A (0 - 100) if < 3 res aligned coord not real.... covera= 40
Coverage for B (0 - 100) if < 3 res aligned coord not real.... coverb= 40
Number of matches to output .................................  maxmch= 10
Output file separate/joint ..................................... sejo= joint
````

Use the following coammnd to execute TBD:
```
./gramm tb
```
This will perform the TBD docking using the specified thresholds in the parameter file `tpar.gr` and will generate the protein-protein complex structures in PDB format. The REMARK section will contain information about templates, as well as scores for structural and sequence alignment. 

Follow the `gramm.log` file for any error or to check completion of a GRAMM run. The common errors are:
````
ERROR: no parameters (scan,tb,refine)
````
The procedure arument was not provided, you should execute `./gramm` with either `scan`, `refine` or `tb`. 
````
ERROR IN OPENING rpar.gr
````
Parameter files `rmol.gr`, `wlist.gr`, `wpar.gr`, and `rpar.gr` (`tpar.gr` for TBD) must be present in working directory.
````
ERROR: no atoms in xxxx.pdb fragment * are selected
````
This error occurs when ATOM coordinates are missing in the provided input structure, `xxxx.pdb`. The GRAMM docking software is optimized and benchmarked for protein-protein interactions and both the receptor and ligand files must contain ATOM records. 

<br>

#### Parallel execution

The GRAMM code is designed for parallel execution and can run on a multiprocessor system using OpenMPI. Use the following command to run GRAMM in parallel execution:
```
mpirun –n X ./gramm XXX   
```
where X is number of processes, XXX is either `scan`, `refine` or `tb`. 

<br>

### Other GRAMM references

[Singh A., Dauzhenka T., Kundrotas P.J., Sternberg M.J.E., Vakser I.A.. 2020, Application of docking methodologies to modeled proteins, Proteins, 88:1180–88.](https://doi.org/10.1002/prot.25889)

[Tovchigrechko, A., Vakser, I.A., 2008, How common is the funnel-like energy landscape in protein-protein interactions? Protein Sci., 10:1572-1583](https://doi.org/10.1110/ps.8701).

[Tovchigrechko, A., Vakser, I.A., 2006, GRAMM-X public web server for protein–protein docking, Nucleic Acids Research, 34:W310–W314.](https://doi.org/10.1093/nar/gkl206)

[Vakser, I.A., 1996, Long-distance potentials: An approach to the multiple-minima problem in ligand-receptor interaction, Protein Eng., 9:37-41.](https://doi.org/10.1093/protein/9.1.37)

[Vakser, I.A., 1995, Protein docking for low-resolution structures, Protein Eng., 8:371-377](https://doi.org/10.1093/protein/8.4.371)

## Contact information

This software is developed by the [Vakser Lab](https://vakserlab.ku.edu/) within [The KU Center for Computational Biology](https://compbio.ku.edu/) at [The University of Kansas](https://www.ku.edu).  Questions can be directed to [gramm@ku.edu](mailto:gramm@ku.edu).  Written correspondence can be directed to the following address:

```
Center for Computational Biology
ATTN: Ilya Vakser
Multidisciplinary Research Building
2030 Becker Drive, Lawrence, KS 66047
```


## License and Disclaimer

**Copyright 1997 - 2025 Vakser Lab**

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

### Third-party software

GRAMM utilizes third-party software, libraries or code, which may be licensed by separate terms, conditions, or 
provisions.  Your use of the third-party software, libraries, or code is subject to the individual terms and 
restrictions of it's associated license, which you are responsible for checking to make sure you can comply with any
terms, conditions, and restrictions prior to your usage of that software.