/*
===============================================================================
                                                                        R1FFT.C
                                            3D discrete Fourier transform (NRC)
===============================================================================
*/
#include <math.h>
 
#define SWAP(a,b) tempr=(a);(a)=(b);(b)=tempr
 
extern float g[];
extern int   npx;
 
void r1fft (int isign)
{
double theta,wi,wpi,wpr,wr,wtemp;           /* Double prec.for trigon.recurr.*/
float  tempi,tempr,wwr,wwi;
long   i1,i2,i3,i2rev,i3rev,ip1,ip2,ip3,ifp1,ifp2,ibit,k1,k2,n,nprev,nrem,ntot;
int    idim;
 
      ntot=(long)(npx*npx*npx); nprev=1l;
      for (idim=3; idim>=1; idim--)
        {
         n=(long)npx; nrem=ntot/(n*nprev);
         ip1=nprev<<1; ip2=ip1*n; ip3=ip2*nrem; i2rev=1l;
         for (i2=1l; i2<=ip2; i2+=ip1)
           {
            if (i2<i2rev)
              {
               for (i1=i2; i1<=i2+ip1-2l; i1+=2l)
                 {
                  for (i3=i1; i3<=ip3; i3+=ip2)
                    {
                     i3rev=i2rev+i3-i2;
                     SWAP(g[i3],g[i3rev]); SWAP(g[i3+1l],g[i3rev+1l]);
                    }
                 }
              }
            ibit=ip2>>1;
            while (ibit>=ip1&&i2rev>ibit) { i2rev-=ibit; ibit>>=1; }
            i2rev+=ibit;
           }
         ifp1=ip1;
         while (ifp1<ip2)
           {
            ifp2=ifp1<<1;
            theta=(double)isign*6.28318530717959/((double)(ifp2/ip1));
            wtemp=sin(0.5*theta); wpr=-2.0*wtemp*wtemp; wpi=sin(theta);
            wr=1.0; wi=0.0;
            for (i3=1l; i3<=ifp1; i3+=ip1)
              {
               for (i1=i3; i1<=i3+ip1-2l; i1+=2l)
                 {
                  for (i2=i1; i2<=ip3; i2+=ifp2)
                    {
                     k1=i2; k2=k1+ifp1;
                     wwr=(float)wr; wwi=(float)wi;
                     tempr=wwr*g[k2]-wwi*g[k2+1l];tempi=wwr*g[k2+1l]+wwi*g[k2];
                     g[k2]=g[k1]-tempr; g[k2+1l]=g[k1+1l]-tempi;
                     g[k1] += tempr; g[k1+1l] += tempi;
                    }
                 }
               wr=(wtemp=wr)*wpr-wi*wpi+wr; wi=wi*wpr+wtemp*wpi+wi;
              }
            ifp1=ifp2;
           }
         nprev*= n;
        }
}
