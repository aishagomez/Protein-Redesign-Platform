/*
===============================================================================
                                                                        R1DIM.H
                                                           Dimensions of arrays
===============================================================================
*/
 
#define  DIM1    30000                         /* No. of atoms in a molecule */

#define  DIM11    5000                         /* No. of resid.in a molecule */

#define  DIMR       20            /* No. of residue types for stat potential */

#define  DIM2      128                         /* No. of pixels at 1D        */

#define  DIM3   300000                         /* No. of orientations        */
 
#define  DIM4       30                         /* No. of peaks retained at   */
                                               /* each orientation           */
/*---------------------------------------------------------------------------*/


#define  DIMG     2*DIM2*DIM2*DIM2+2                             /* G arrays */
 
#define  DIMP     DIM3*DIM4                            /* No.of peaks (total)*/
 
#define  DIMS     DIMP
#if      DIMS  <  DIM1
#define  DIMS     DIM1
#endif                                                 /* Sort:max(DIM1,DIMP)*/
 
/*---------------------------------------------------------------------------*/
