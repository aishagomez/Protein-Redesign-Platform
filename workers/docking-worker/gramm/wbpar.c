/*
===============================================================================
                                                                        WBPAR.C
                                                          Trajectory Parameters
===============================================================================
*/

void wbpar(int it,float *rcc,float *ro,float *devr,float *devt)
{
/*    if (it== 1) { *rcc= 3.5; *ro= 3.;   *devr= 10.; *devt= 3.5; } */
/*    if (it== 1) { *rcc= 3.0; *ro= 4.2;  *devr=  8.; *devt= 3.0; } */
/*    if (it== 1) { *rcc= 2.5; *ro= 5.0;  *devr=  6.; *devt= 2.5; } */
/*    if (it== 1) { *rcc= 2.0; *ro= 10.;  *devr=  4.; *devt= 2.0; } */

      if (it== 1) { *rcc= 2.0; *ro= 3.0;  *devr=  3.; *devt= 1.5; }

/*    if (it== 4) { *rcc=  0.; *ro= 30.;  *devr=  2.; *devt= 1.0; } */
/*    if (it== 5) { *rcc=  0.; *ro= 30.;  *devr=  1.; *devt= 0.5; } */
}
