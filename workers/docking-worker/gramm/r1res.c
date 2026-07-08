/*
===============================================================================
                                                                        R1RES.C
                                                         Output of SCAN results
===============================================================================
*/
#include <stdio.h>
#include <string.h>
#include <time.h>
 
#define  FR         fprintf(fres,
#define  ULINE      FR"___________________________")
#define  UNDERLINE  FR"\n");ULINE;ULINE
#define  USER       FR" ")
 
void r1us4(int *,float,float,float,float,float,float,int *);
void r1us6(int,float,float,float);
/* void r1us60(int); */

extern float g[];
extern float xb0,yb0,zb0;
extern long  sh[],in[],ino[],NG2,NG2_2;
extern int   orn[][3],pk[],nuro[],npx,ai,ctiv,repr,range,maxa,nuron;
extern int   ier1;
extern char  mmode[],antip[];
extern FILE  *fres;
 
void r1res (char *name_a,char *name_b,char *fna,char *fnb,char *cha,char *chb,
            float *ro,float th,long maxm,float eta,float eta3,float xb,
            float yb,float zb,float x1,float y1,float z1,int npek,int npr,
            float rpi,int npa,int npb,int *us)
{
float  xt,yt,zt,a,b,g,u,v,w,dis,ro2,ro4,ro5;
long   s1,s2,i,j,k,npxl,inr,inro;
int    ir,irr,fi,mm,hes,ire;
time_t t;
char   s[80];

      FR"\nG R A M M   v2.0   prerelease");
      FR"\nGlobal Range Molecular Matching");

      time(&t); strcpy(s,ctime(&t));
      FR"\n                                          %c%c%c %c%c, %c%c%c%c",
         s[4],s[5],s[6],s[8],s[9],s[20],s[21],s[22],s[23]);

      UNDERLINE;
      FR"\n[molecules]");
      FR"\n%s  ( %s fragment %s %5d",name_a,fna,cha,npa);
      if (repr==2) FR" CA"); FR" atoms)");
      FR"\n%s  ( %s fragment %s %5d",name_b,fnb,chb,npb);
      if (repr==2) FR" CA"); FR" atoms)");
      UNDERLINE;

      if(mmode[0]=='h') 
        {
         FR"\n\nHelix matching  (");
         if (antip[0]=='a') FR"anti"); FR"parallel, max.angle %d deg)",maxa);
        }  
      else FR"\n\nGeneric matching");

      FR"\nPotential range equal to");
      if(range) FR" grid step"); else FR" atoms radii");
      ro2=-ro[2]*eta3; ro4=-ro[4]*eta3; ro5=-ro[5]*eta3;
      FR" (%4.1f,%4.1f,%4.1f)",ro2,ro4,ro5);

      if(ctiv) FR"\nCumulative"); else FR"\nNon-cumulative"); FR" projection");

      if(repr==1) FR" (hydrophobic only)");  else { 
      if(repr==2) FR" (c-alpha only)");      else {
                  FR" (all atoms)");             }}

      FR"\nGrid step ............................ %-3.1f",eta);

      if (us[1])
      FR"\nGrid size (forced) ................... %-4d",npx);
      else
      FR"\nGrid size ............................ %-4d",npx);

      FR"\nEnergy values are divided by ......... %-4.1f",eta3);
/*    FR"\nEnergy threshold (rel.) .............. %-4.2f",th);     */
      FR"\nNo.of matches to output .............. %-5ld",maxm);
      if (ai==0) FR"\n(%d for a single orientation)",npr);
/*    FR"\nNo.of matches to store per orient. ... %-4d",npr);      */  
      FR"\nAngle interv.for rot.(deg) ........... %-4d",ai);
/*    FR"\nRadius of match identity (pix) ....... %-3.1f",rpi);    */

      mm=maxm; if (mm>npek) mm=npek;
/*    FR"\nNo.of matches retained ............... %-4d",mm);       */
      if (us[34])
      FR"\nAxis atom number ..................... %-4d",us[34]);
      if (us[35])
      FR"\n[initial_angles]  %d  %d  %d",us[36],us[37],us[38]);
      if (mmode[0]=='o')
        {
         FR"\nBinding residues:"); 
         for (ire=1; ire<=nuron; ire++) FR" %d",nuro[ire]);
        }
      if (us[44]) FR"\nMol.B init.coord: %4.1f %4.1f %4.1f",xb0,yb0,zb0);

      UNDERLINE;
      FR"\n\n  No.  Energy   Rotation           Translation");
      if (us[29]) FR"         Shift[pix]");
      if (us[34]) FR"        Phi");
      FR  "\n        (-)");
      if (us[29]) FR"                                            from proj.");
      UNDERLINE;

      FR"\n [match]");

      dis=1.5*eta;                /* Maximum dislocation from Xray structure */
      dis=dis*dis;

      ir=irr=0; npxl=(long)npx;
      while(1)
        {
         ir++;
         inr=in[ir]; inro=ino[inr];
         s1=(sh[inr]-1l)/2l;  s2=s1%(NG2_2/2l);
         k=-s1/(NG2_2/2l); j=-s2/(NG2/2l); i=-s2%(NG2/2l);
         if(i<-npxl/2l)i+=npxl; if(j<-npxl/2l)j+=npxl; if(k<-npxl/2l)k+=npxl;
         xt=((float)i)*eta+xb; yt=((float)j)*eta+yb; zt=((float)k)*eta+zb;
         a=(float)orn[inro][0]; b=(float)orn[inro][1]; g=(float)orn[inro][2];
/*--------------------------------------------------- Axis angle calculation */
         if (us[34]) { u=x1-xb0;v=y1-yb0;w=z1-zb0; r1us4(us,a,b,g,u,v,w,&fi); }
/*-------------------------------------------------- Shift check for helices */
         hes=3*(npx/8);
         if (mmode[0]=='h')
           {
            if ((i<hes)&&(i>-hes)&&(j<hes)&&(j>-hes)&&(k<hes)&&(k>-hes)) irr++;
            else continue;
           }
         else irr++;
/*--------------------------------------------- Check maximum number of hits */
         if (irr>mm) break;
/*------------------------------- Criterion 1, helix, interface-noninterface */
/*      would be more logical if implemented at the refinement stage (w0crd) */
         if (us[44]) { r1us6(irr,xt,yt,zt);  if (ier1) return; }
/*       if (us[45]&&(ir==1)) { r1us60(npa); if (ier1) return; } */
/*---------------------------------------------------------------------------*/

         FR"\n%5d  %4d  %4.0f %4.0f %4.0f",irr,pk[ir],a,b,g);
         FR"  %7.2f %7.2f %7.2f",xt,yt,zt);
         if (us[29]) FR"  %4ld %4ld %4ld  ",i,j,k);
         if (us[34]&&((xt*xt)<dis)&&((yt*yt)<dis)&&((zt*zt)<dis)) FR" %4d",fi);
        }
}
