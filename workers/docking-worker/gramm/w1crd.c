/*
===============================================================================
                                                                        W1CRD.C
                                            Generate coordinates from RES files
===============================================================================
*/
#include <stdlib.h>
#include <math.h>
#include "r1gen.h"

extern float x[],y[],z[],x_1[],y_1[],z_1[];
extern float al[],bl[],gl[],ul[],vl[],wl[];
extern float xk[],yk[],zk[];
extern long  ind[];

void w1crd(int im,int ic,int npa,int npb,float *cma,float *cmb,float *cmbb,
           float *cm,float ai,float bi,float gi,int *us)
{
float a,b,g,u,v,w,ap,bp,gp,sa,sb,sg,ca,cb,cg,xr,yr,zr,xi,yi,zi;
float raa,rraa,cmi1,cmi2,cmi3;
float a11,a12,a13,a21,a22,a23,a31,a32,a33;
float ai11,ai12,ai13,ai21,ai22,ai23,ai31,ai32,ai33;
int   i,j,imd,npbb;

      raa=4.5; raa=raa*raa;                 /* distance for atoms in contact */

      imd=ind[im];                                        /* re-sorted index */
      a=al[imd]; b=bl[imd]; g=gl[imd]; u=ul[imd]; v=vl[imd]; w=wl[imd];

/*------------------ Precalculate rotational parameters for initial rotation */
      ap=ai*0.017453; bp=bi*0.017453; gp=gi*0.017453;

      sa=(float)sin((double)ap); ca=(float)cos((double)ap);
      sb=(float)sin((double)bp); cb=(float)cos((double)bp);
      sg=(float)sin((double)gp); cg=(float)cos((double)gp);

      ai11=cg*ca;          ai12=cg*sa;          ai13=-sg;
      ai21=sb*sg*ca-cb*sa; ai22=sb*sg*sa+cb*ca; ai23= cg*sb;
      ai31=cb*sg*ca+sb*sa; ai32=cb*sg*sa-sb*ca; ai33= cg*cb;

/*--------------------------------------- Precalculate rotational parameters */
      ap=a*0.017453; bp=b*0.017453; gp=g*0.017453;

      sa=(float)sin((double)ap); ca=(float)cos((double)ap);
      sb=(float)sin((double)bp); cb=(float)cos((double)bp);
      sg=(float)sin((double)gp); cg=(float)cos((double)gp);

      a11=cg*ca;          a12=cg*sa;          a13=-sg;
      a21=sb*sg*ca-cb*sa; a22=sb*sg*sa+cb*ca; a23= cg*sb;
      a31=cb*sg*ca+sb*sa; a32=cb*sg*sa-sb*ca; a33= cg*cb;
/*---------------------------------------------------------- Center of mol.A */
      if ((im==1)||(ic==0))
        {
         cma[1]=cma[2]=cma[3]=0.;
         for (i=1;i<=npa;i++) { cma[1]+=x_1[i];cma[2]+=y_1[i];cma[3]+=z_1[i]; }
         cma[1]/=((float)npa); cma[2]/=((float)npa); cma[3]/=((float)npa);

/*-------------------------------- Mol.B: center of mol.and center of b.site */

         cmb[1]=cmb[2]=cmb[3]=cmbb[1]=cmbb[2]=cmbb[3]=0.; npbb=0;
         for (i=1; i<=npb; i++) { cmb[1]+=x[i]; cmb[2]+=y[i]; cmb[3]+=z[i]; }
         cmb[1]/=((float)npb); cmb[2]/=((float)npb); cmb[3]/=((float)npb);
         if (us[41]&&us[42])
           {
            for (i=1; i<=npb; i++)
              {
               for (j=1; j<=npa; j++)
                 {
                  rraa=(x[i]-x_1[j])*(x[i]-x_1[j])+
                       (y[i]-y_1[j])*(y[i]-y_1[j])+
                       (z[i]-z_1[j])*(z[i]-z_1[j]);
                  if (rraa<=raa)
                    { npbb++; cmbb[1]+=x[i]; cmbb[2]+=y[i]; cmbb[3]+=z[i]; }
                 }
              }
            cmbb[1]/=((float)npbb);
            cmbb[2]/=((float)npbb);
            cmbb[3]/=((float)npbb);
           }
        }
/*--------------------------------------------------------- Mol.B processing */
      cmi1=cmi2=cmi3=0.; npbb=0;                          /* pred.lig.CM&CMB */

      for (i=1; i<=npb; i++)
        {
         xr=x[i]-cmb[1]; yr=y[i]-cmb[2]; zr=z[i]-cmb[3];

         xi=ai11*xr+ai12*yr+ai13*zr;                     /* initial rotation */
         yi=ai21*xr+ai22*yr+ai23*zr;
         zi=ai31*xr+ai32*yr+ai33*zr;

         xk[i]=a11*xi+a12*yi+a13*zi+u+cmb[1];               /* real rotation */
         yk[i]=a21*xi+a22*yi+a23*zi+v+cmb[2];
         zk[i]=a31*xi+a32*yi+a33*zi+w+cmb[3];

         if (us[41]&&us[42])
           {
            for (j=1; j<=npa; j++)
              {
               rraa=(xk[i]-x_1[j])*(xk[i]-x_1[j])+
                    (yk[i]-y_1[j])*(yk[i]-y_1[j])+
                    (zk[i]-z_1[j])*(zk[i]-z_1[j]);
               if (rraa<=raa)
                 { npbb++; cmi1+=xk[i]; cmi2+=yk[i]; cmi3+=zk[i]; break; }
              }
           }
         else { cmi1+=xk[i]; cmi2+=yk[i]; cmi3+=zk[i]; }
        }
      if (us[42])           /* center of mass for predicted ligand positions */
        {
         if (us[41])
           {cmi1/=((float)npbb);cmi2/=((float)npbb);cmi3/=((float)npbb);}
         else
           {cmi1/=((float)npb); cmi2/=((float)npb); cmi3/=((float)npb); }
         if (us[42]<0)                                   /* no shift for all */
           { cm[1]=cmi1;  cm[2]=cmi2;  cm[3]=cmi3; }
         else
           {
            if ((im==1)||(ic==0))                        /* no shift for 1st */
              { cm[1]=cmi1; cm[2]=cmi2; cm[3]=cmi3; }
            else                           /* random shift with us[42] limit */
              {
               if (VRAND()<0.5) cm[1]=cmi1-(float)us[42]*VRAND();
               else             cm[1]=cmi1+(float)us[42]*VRAND();
               if (VRAND()<0.5) cm[2]=cmi2-(float)us[42]*VRAND();
               else             cm[2]=cmi2+(float)us[42]*VRAND();
               if (VRAND()<0.5) cm[3]=cmi3-(float)us[42]*VRAND();
               else             cm[3]=cmi3+(float)us[42]*VRAND();
              }
           }
        }
}
