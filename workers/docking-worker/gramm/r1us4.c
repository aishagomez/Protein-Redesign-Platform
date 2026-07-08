/*
===============================================================================
                                                                        R1US4.C
                                                                  User's module
                                                         Axis angle calculation
===============================================================================
*/
#include <stdio.h>
#include <math.h>

void r1us4 (int *us,float a,float b,float g,float u,float v,float w,int *fi)
{
float up,vp,wp,sa,sb,sg,ca,cb,cg,anco,anaco;
float a11,a12,a13,a21,a22,a23,a31,a32,a33,ui,vi,wi;
float ai,bi,gi,ai11,ai12,ai13,ai21,ai22,ai23,ai31,ai32,ai33;

/*--------------------------------------------------------- Initial rotation */
      ai=((float)us[36])*0.017453; 
      bi=((float)us[37])*0.017453; 
      gi=((float)us[38])*0.017453;

      sa=(float)sin((double)ai); ca=(float)cos((double)ai);
      sb=(float)sin((double)bi); cb=(float)cos((double)bi);
      sg=(float)sin((double)gi); cg=(float)cos((double)gi);

      ai11=cg*ca;          ai12=cg*sa;          ai13=-sg;
      ai21=sb*sg*ca-cb*sa; ai22=sb*sg*sa+cb*ca; ai23= cg*sb;
      ai31=cb*sg*ca+sb*sa; ai32=cb*sg*sa-sb*ca; ai33= cg*cb;

      ui=ai11*u+ai12*v+ai13*w;
      vi=ai21*u+ai22*v+ai23*w;
      wi=ai31*u+ai32*v+ai33*w;
/*-------------------------------------------------------- Regular rotation */
      a*=0.017453; b*=0.017453; g*=0.017453;

      sa=(float)sin((double)a); ca=(float)cos((double)a);
      sb=(float)sin((double)b); cb=(float)cos((double)b);
      sg=(float)sin((double)g); cg=(float)cos((double)g);

      a11=cg*ca;          a12=cg*sa;          a13=-sg;
      a21=sb*sg*ca-cb*sa; a22=sb*sg*sa+cb*ca; a23= cg*sb;
      a31=cb*sg*ca+sb*sa; a32=cb*sg*sa-sb*ca; a33= cg*cb;

      up=a11*ui+a12*vi+a13*wi;
      vp=a21*ui+a22*vi+a23*wi;
      wp=a31*ui+a32*vi+a33*wi;

      anco=(u*up+v*vp+w*wp)/(u*u+v*v+w*w);
      anaco=(float)acos((double)anco);
   
      *fi=(int)(anaco*57.3); 
}
