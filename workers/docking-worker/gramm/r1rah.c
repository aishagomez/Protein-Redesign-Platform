/*
===============================================================================
                                                                        R1RAH.C
                                                Atomic radii & hydrophobicities
===============================================================================
*/
#include <string.h>
 
extern int   repr;
 
void r1rah (int npa,int npb,float *ram)
{
float hh[20],rr[20];
float rm;
int   ip,npar;
char  typ[20][4];
 
/*---------------------------------------------------------
 16    ES    RV       /   ES    RV
C6    0.00  2.00      /  0.00  1.60 c-alpha
C7    0.00  1.67      / -0.60  1.67 CO,COO,CONH
C8    1.00  1.75      /  0.47  1.75 tert.H-less
N13   0.00  1.80      / -0.90  1.54 amin
N14   0.00  1.80      / -0.90  1.78 amid
O17   0.00  1.49      / -1.96  1.49 CO,COOH
O17-  0.00  1.49      /-13.90  1.49 CO,COOH
O18   0.00  1.60      / -2.64  1.44 OH,(CO)OH
S20   1.00  1.60      /  1.02  1.84 sulfur
CHR   1.00  1.91      /  0.47  1.91 CH aromatic
CH    1.00  2.21      /  0.98  2.21 united atom
CH2   1.00  1.99      /  1.57  1.99 united atom
CH3   1.00  1.98      /  2.88  1.98 united atom
P     0.00  1.90      /     ?  1.90 phosphate
NR    1.00  1.80      /  0.5(?)1.80(?)N aromatic
X     0.00  1.80      /             unknown
----------------------------------------------------------*/

      strcpy(typ[ 1], "C6  " ); hh[ 1]= 0.; rr[ 1]= 2.00;   
      strcpy(typ[ 2], "C7  " ); hh[ 2]= 0.; rr[ 2]= 1.67;   
      strcpy(typ[ 3], "C8  " ); hh[ 3]= 1.; rr[ 3]= 1.75;   
      strcpy(typ[ 4], "N13 " ); hh[ 4]= 0.; rr[ 4]= 1.80;   
      strcpy(typ[ 5], "N14 " ); hh[ 5]= 0.; rr[ 5]= 1.80;   
      strcpy(typ[ 6], "O17 " ); hh[ 6]= 0.; rr[ 6]= 1.49;   
      strcpy(typ[ 7], "O17-" ); hh[ 7]= 0.; rr[ 7]= 1.49;   
      strcpy(typ[ 8], "O18 " ); hh[ 8]= 0.; rr[ 8]= 1.60;   
      strcpy(typ[ 9], "S20 " ); hh[ 9]= 1.; rr[ 9]= 1.60;   
      strcpy(typ[10], "CHR " ); hh[10]= 1.; rr[10]= 1.91;   
      strcpy(typ[11], "CH  " ); hh[11]= 1.; rr[11]= 2.21;   
      strcpy(typ[12], "CH2 " ); hh[12]= 1.; rr[12]= 1.99;   
      strcpy(typ[13], "CH3 " ); hh[13]= 1.; rr[13]= 1.98;   
      strcpy(typ[14], "P   " ); hh[14]= 0.; rr[14]= 1.90;   
      strcpy(typ[15], "NR  " ); hh[15]= 1.; rr[15]= 1.80;   
      strcpy(typ[16], "X   " ); hh[16]= 0.; rr[16]= 1.80;   

      npar=16;
/*----------------------------------------------- Assign parameters to atoms */

      if((repr==0)||(repr==2)){for(ip=1;ip<=npar;ip++)hh[ip]=1.;} /*all/hydro*/

                                                                    /* Mol.A */
      r1rha(typ,hh,rr,npar,npa,0,&rm); *ram=rm;
                                                                    /* Mol.B */
      r1rha(typ,hh,rr,npar,npb,1,&rm); if(*ram<rm) *ram=rm;
}
