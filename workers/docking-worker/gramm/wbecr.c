/*
===============================================================================
                                                                        WBECR.C
                                                    External coordinates search
                                                              Grid minimization
===============================================================================
Energy function does not have arguments-coordinates because in grid 
minimization one can optimize speed by spreading function calculation thru the
search (outside cycles). In other minimization protocols (e.g. simplex)
search and function have to be separate - the energy function should have 
arguments-coordinates (has to include rotation/translation calculation in the 
energy function).
*/
#include <math.h>
#include <stdio.h>

void wbene(int,int,int,float,float,float *);

extern float xi[],yi[],zi[],xo[],yo[],zo[];
extern float xr[],yr[],zr[];
extern float xa[],ya[],za[],xb[],yb[],zb[];
extern int   inta[],intb[];
extern int   myProc, nProc;    /*PRLL*/

void wbecr(int mbak,int npa,int npb,float rcc,float ro,float devr,float devt,
           float *cmb,float *en,int *us)
{
float ia,ib,ig,ix,iy,iz,da,db,dg,dx,dy,dz,xl,yl,zl;
float a,b,g,sa,sb,sg,ca,cb,cg,a11,a12,a13,a21,a22,a23,a31,a32,a33;
float ene;
int   l;

/*----------------------------------------------------------- Initial values */
      for (l=1; l<=npb; l++) { xi[l]=xb[l]; yi[l]=yb[l]; zi[l]=zb[l]; }
      *en=-30000.;
      if ((us[2]==2)&&(nProc==1))
        { 
         wbene(mbak,npa,npb,rcc,ro,&ene);
         for (l=1; l<=npb; l++) { xo[l]=xi[l]; yo[l]=yi[l]; zo[l]=zi[l]; }
         printf("  %5.0f ... ",ene);
        }
/*---------------------------------------------------- Rotational deviations */
      for (ia=-devr; ia<=(devr+0.001); ia+=devr)
        {
         for (ib=-devr; ib<=(devr+0.001); ib+=devr)
           {
            for (ig=-devr; ig<=(devr+0.001); ig+=devr)
              {
               a=ia*0.017453; b=ib*0.017453; g=ig*0.017453;
 
               sa=(float)sin((double)a); ca=(float)cos((double)a);
               sb=(float)sin((double)b); cb=(float)cos((double)b);
               sg=(float)sin((double)g); cg=(float)cos((double)g);
 
               a11=cg*ca;          a12=cg*sa;           a13=-sg;
               a21=sb*sg*ca-cb*sa; a22=sb*sg*sa+cb*ca;  a23= cg*sb;
               a31=cb*sg*ca+sb*sa; a32=cb*sg*sa-sb*ca;  a33= cg*cb;
 
               for (l=1; l<=npb; l++)
                 {
                  xl=xo[l]-cmb[1]; yl=yo[l]-cmb[2]; zl=zo[l]-cmb[3];
 
                  xr[l]=a11*xl+a12*yl+a13*zl;
                  yr[l]=a21*xl+a22*yl+a23*zl;
                  zr[l]=a31*xl+a32*yl+a33*zl;
 
                  xr[l]+=cmb[1]; yr[l]+=cmb[2]; zr[l]+=cmb[3];
                 }
/*------------------------------------------------- Translational deviations */
               for (ix=-devt; ix<=(devt+0.001); ix+=devt)
                 {
                  for (l=1; l<=npb; l++) xi[l]=xr[l]+ix;
                  for (iy=-devt; iy<=(devt+0.001); iy+=devt)
                    {
                     for (l=1; l<=npb; l++) yi[l]=yr[l]+iy;
                     for (iz=-devt; iz<=(devt+0.001); iz+=devt)
                       {
                        for (l=1; l<=npb; l++) zi[l]=zr[l]+iz;
/*------------------------------------------------------- Energy calculation */

                        wbene(mbak,npa,npb,rcc,ro,&ene);

/*---------------------------------------------------------------------------*/
                        if (ene>(*en))
                          {
                           *en=ene;
                           for (l=1; l<=npb; l++)
                             { xb[l]=xi[l]; yb[l]=yi[l]; zb[l]=zi[l]; }
                           da=ia; db=ib; dg=ig; dx=ix; dy=iy; dz=iz;
                          }
                       }
                    }
                 }
              }
           }
        }
      if ((us[2]==2)&&(nProc==1))
         printf("%5.0f  %4.0f %4.0f %4.0f %5.1f %5.1f %5.1f",
                *en,da,db,dg,dx,dy,dz);
}
