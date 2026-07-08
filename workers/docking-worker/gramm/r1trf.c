/*
===============================================================================
                                                                        R1TRF.C
                                        Coordinate transform and min/max limits
===============================================================================
*/
#include <stdio.h>

extern float x[],y[],z[],x_1[],y_1[],z_1[],ra[][2];
extern int   npx;
 
void r1trf (int npa,int npb,float eta,float xa,float ya,float za,float *xb,
            float *yb,float *zb,float *cmb,int *us)
{
float cma;
int   l;
 
      for (l=1; l<=npa; l++)
        {
         ra[l][0]/=eta;
         x[l]=(x[l]-xa)/eta; y[l]=(y[l]-ya)/eta; z[l]=(z[l]-za)/eta;
        }

      for (l=1; l<=npa; l++)                         
        { x[l]+=(float)npx/2.; y[l]+=(float)npx/2.; z[l]+=(float)npx/2.; }
 
       cma=(float)npx/2.;                        /* Mol.A center on the grid */
      *cmb=(float)npx/2.;                        /* Mol.B center on the grid */
                                                 
      for (l=1; l<=npb; l++)
        {
         ra[l][1]/=eta;
                                      /* + Shi             */
         x_1[l]=(x_1[l]-(*xb))/eta+(*cmb)+((float)us[30])/10.;
         y_1[l]=(y_1[l]-(*yb))/eta+(*cmb)+((float)us[31])/10.;
         z_1[l]=(z_1[l]-(*zb))/eta+(*cmb)+((float)us[32])/10.;
        }
                                    /* (b_proj - b_real) + (a_real - a_proj) */
      *xb=eta*((*cmb)-cma)+xa-(*xb);
      *yb=eta*((*cmb)-cma)+ya-(*yb);
      *zb=eta*((*cmb)-cma)+za-(*zb);
}
