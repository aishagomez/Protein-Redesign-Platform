/*
===============================================================================
                                                                        R1DIG.C
                                                             Molecule Digitizer
===============================================================================
*/
#include "r1gen.h"
 
extern float g[];
extern float x[],y[],z[],ra[][2],hy[][2];
extern long  NG2,NG2_2;
extern int   rnber[][2],inn[][2],nuro[];
extern int   npx,range,ctiv,nuron,nurtog;
 
void r1dig (float r,int np,int hc,float ro,int m,int fl)
{
float r2,rr,xl,yl,zl,ix,jy,kz,ix2,jy2,kz2,iyz2,ixyz2;
long  i,j,k,xlmin,xlmax,ylmin,ylmax,zlmin,zlmax;
int   l,li,ir,tgg;
 
      for (l=1; l<=np; l++)
        { 
         li=inn[l][m];

/*       if((repr==2)&&(strncmp(atmnam[li][m]," CA ",4)!=0))continue; */

         if (nurtog)                  /* Check binding site (overlap) */
           {
            tgg=0;
            for (ir=1; ir<=nuron; ir++)
              { if (rnber[li][m]==nuro[ir]) { tgg=1; break; }}
            if (tgg) continue;
           }

         if (range) rr=1.; else rr=ra[li][m];
         rr+=r; r2=rr*rr;

         xl=x[li]; yl=y[li]; zl=z[li];
         xlmax=(long)((int)xl+hc); xlmin=xlmax-(long)(hc+hc-1);
         ylmax=(long)((int)yl+hc); ylmin=ylmax-(long)(hc+hc-1);
         zlmax=(long)((int)zl+hc); zlmin=zlmax-(long)(hc+hc-1);
         if (xlmin<1) xlmin=1; if (xlmax>npx) xlmax=npx;
         if (ylmin<1) ylmin=1; if (ylmax>npx) ylmax=npx;
         if (zlmin<1) zlmin=1; if (zlmax>npx) zlmax=npx;
         for (k=zlmin; k<=zlmax; k+=1l)
           {
            kz=(float)k-zl; kz2=kz*kz;
            for (j=ylmin; j<=ylmax; j+=1l)
              {
               jy=(float)j-yl; jy2=jy*jy; iyz2=jy2+kz2;
               for (i=xlmin; i<=xlmax; i+=1l)
                 { 
                  ix=(float)i-xl; ix2=ix*ix; ixyz2=ix2+iyz2;
 
                  if (ixyz2 < r2)
                    {
                     if(ctiv)
                       {
                        if(fl) g[R(i,j,k)]+=(ro*hy[li][m]);
                        else   g[R(i,j,k)]+= ro;
                       }
                     else
                       {
                        if(fl) g[R(i,j,k)]=ro*hy[li][m];
                        else   g[R(i,j,k)]=ro;
                       }
                    }
                 }
              }
           }
        }
}
