/*
===============================================================================
                                                                        R1RAM.C
                                                 Radius of molecule calculation
===============================================================================
*/
#include <math.h>
 
extern float x[],y[],z[],x_1[],y_1[],z_1[];
 
void r1ram (int npa,int npb,float *rma,float *rmb,
            float *xa,float *ya,float *za,
            float *xb,float *yb,float *zb)
{
float xmn,xmx,ymn,ymx,zmn,zmx,rx,ry,rz,sx,sy,sz,rl,xl,yl,zl;
int   l;
                                                                    /* Mol.A */
                                         /* Max. size in X,Y or Z directions */
      xmn=ymn=zmn=10000.; xmx=ymx=zmx=-10000.;
      for (l=1; l<=npa; l++)
        {
         if (xmn>x[l]) xmn=x[l];
         if (xmx<x[l]) xmx=x[l];
         if (ymn>y[l]) ymn=y[l];
         if (ymx<y[l]) ymx=y[l];
         if (zmn>z[l]) zmn=z[l];
         if (zmx<z[l]) zmx=z[l];
        }
      *xa=(xmn+xmx)/2.; *ya=(ymn+ymx)/2.; *za=(zmn+zmx)/2.;
      rx =(xmx-xmn)/2.; ry =(ymx-ymn)/2.; rz =(zmx-zmn)/2.;
      *rma=rx;
      if (*rma<ry) *rma=ry;
      if (*rma<rz) *rma=rz;
 
                                                                    /* Mol.B */
                /* Distance between center of mol. and the most distant atom */
 
      sx=sy=sz=(*rmb)=0.;
      for (l=1; l<=npb; l++) { sx+=x_1[l]; sy+=y_1[l]; sz+=z_1[l]; }
      *xb=sx/((float)npb);*yb=sy/((float)npb);*zb=sz/((float)npb);
      for (l=1; l<=npb; l++)
        {
         xl=x_1[l]-(*xb); yl=y_1[l]-(*yb); zl=z_1[l]-(*zb);
         rl=(float)sqrt((double)(xl*xl+yl*yl+zl*zl));
         if (*rmb<rl) *rmb=rl;
        }
}
