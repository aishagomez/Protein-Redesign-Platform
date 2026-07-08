/*
===============================================================================
                                                                        R1US3.C
                                                    Molecule B initial rotation
===============================================================================
*/
#include <math.h>
 
extern float x_1[],y_1[],z_1[];
 
void r1us3 (int *us,float cmb,int npb)
{
float a,b,g,sa,sb,sg,ca,cb,cg;
float a11,a12,a13,a21,a22,a23,a31,a32,a33;
float xl,yl,zl;
int   l;
 
      a=((float)us[36])*0.017453;
      b=((float)us[37])*0.017453;
      g=((float)us[38])*0.017453;
 
      sa=(float)sin((double)a); ca=(float)cos((double)a);
      sb=(float)sin((double)b); cb=(float)cos((double)b);
      sg=(float)sin((double)g); cg=(float)cos((double)g);
 
      a11=cg*ca;          a12=cg*sa;           a13=-sg;
      a21=sb*sg*ca-cb*sa; a22=sb*sg*sa+cb*ca;  a23= cg*sb;
      a31=cb*sg*ca+sb*sa; a32=cb*sg*sa-sb*ca;  a33= cg*cb;
 
      for (l=1; l<=npb; l++)
        {
         xl=x_1[l]-cmb; yl=y_1[l]-cmb; zl=z_1[l]-cmb;
 
         x_1[l]=a11*xl+a12*yl+a13*zl;
         y_1[l]=a21*xl+a22*yl+a23*zl;
         z_1[l]=a31*xl+a32*yl+a33*zl;
 
         x_1[l]+=cmb; y_1[l]+=cmb; z_1[l]+=cmb;
        }
}
