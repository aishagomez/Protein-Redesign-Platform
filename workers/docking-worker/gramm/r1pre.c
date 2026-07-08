/*
===============================================================================
                                                                        R1PRE.C
                                                       Parameters preprocessing
===============================================================================
*/
#include <stdio.h>
#include <string.h>

void r1rah(int,int,float *);
void r1ram(int,int,float *,float *,float *,float *,float *,
           float *,float *,float *);
void r1trf(int,int,float,float,float,float,float *,float *,float *,float *,
           int *);
void r1prr(long *);
 
extern float x[],y[],z[],h1uvw[],ng3,xb0,yb0,zb0,xa1,ya1,za1,xa2,ya2,za2;
extern long  NG2,NG2_2,NG2_3;
extern int   npx,range,repr,ctiv,ier1,ier2;
extern char  mmode[],atmnam[][2][4];
extern FILE  *fflog;

extern int myProc, nProc;

void r1pre(int npa,int npb,float *cmb,int *hca,int *hcb,long *nor,float *eta,
           float *rpi,float *xb,float *yb,float *zb,float *ro,float *eta3,
           char *name_a,char *name_b,int *us)
{
float xa,ya,za,rma,rmb,ram;
int   nx,ca1,ca2;

                                          /* Atomic radii & hydrophobicities */
      r1rah(npa,npb,&ram);
                                                     /* max.molecular radius */
      r1ram(npa,npb,&rma,&rmb,&xa,&ya,&za,xb,yb,zb);

      if(range) ram=0.;      /* should be ram=*eta, however, consistency ... */
      rma+=ram; rmb+=ram;
      xb0=(*xb); yb0=(*yb); zb0=(*zb);

                                                                      /* npx */
      if(us[1]==0) 
        {
         if (mmode[0]=='h')  nx=(int)(2.*(rma+(rmb/2.))/(*eta)) + 1;
         else                nx=(int)(2.*(rma+ rmb    )/(*eta)) + 1;
         if (nx<= 16) npx= 16;  else {
         if (nx<= 32) npx= 32;  else {
         if (nx<= 64) npx= 64;  else {
         if (nx<=128) npx=128;  else {
	     fprintf(fflog,"\n*** ERROR: for %s and %s molecules",name_a,name_b); 
         fprintf(fflog," the %4.1f step is too small for the max",*eta);
         fprintf(fflog," 128x128x128 grid\n"); ier2=1; return;  }}}}

         if (us[43]&&(npx>=128)&&(myProc==0)) 
           {
            fprintf (fflog,"\nGrid %dx%dx%d (%s and %s) skipped",
                             npx,npx,npx,name_a,name_b);
            if(us[2]) { fflush(stdout); 
                        printf("\nGrid %dx%dx%d (%s and %s) skipped",
                                npx,npx,npx,name_a,name_b); }
            ier2=1; return;
           }
         if(myProc==0)
           {
            fprintf (fflog,"\nGrid %dx%dx%d (%s and %s)",
                             npx,npx,npx,name_a,name_b);
            if(us[2]) { fflush (stdout); printf("\nGrid %dx%dx%d (%s and %s)",
                                                npx,npx,npx,name_a,name_b); }
           }
        }
      else npx=us[1];

                                                      /* NG2,NG2_2,NG2_3,ng3 */
      NG2=(long)(2*npx); NG2_2=(long)(2*npx*npx);
      NG2_3=(long)(2*npx*npx*npx); ng3=(float)(npx*npx*npx);


                    /* normalize mol.A projection (for future energy values) */
      if ((mmode[0]=='d')||(mmode[0]=='h'))              /* docking or helix */
        {
         if (repr==2)            *eta3=(*eta);
         else { if (*eta>=50.)   *eta3=(*eta);
         else { if (*eta>=4. )   *eta3=(*eta)*(*eta);
         else                    *eta3=(*eta)*(*eta)*(*eta)*(*eta)/10.;   }}
        }
      else                                                        /* overlap */
        {
         if (ctiv==0) *eta3=1./(*eta);
         else         *eta3=10.;
        }

      ro[2]/=(*eta3); ro[3]=ro[4]/=(*eta3); ro[5]/=(*eta3);

                                                                  /* hca,hcb */
      *hca=(int)(ram/(*eta)+1.); *hcb=(int)(ram/(*eta)+1.);

                                                                      /* rpi */
      *rpi=(*rpi)/(*eta);                                             

      ca1=1;                                   /* Terminal CA atoms of mol.A */
      while(1)
        {
         if (strncmp(atmnam[ca1][0]," CA ",4)!=0)
           {
            ca1++; if (ca1>=npa) { ca1=1; break; }    /* in case no CA found */
           }
         else break;
        }
      ca2=npa;
      while(1)
        {
         if (strncmp(atmnam[ca2][0]," CA ",4)!=0)
           {
            ca2--; if (ca2<=1) { ca2=npa; break; }    /* in case no CA found */
           }
         else break;
        }
                                     /* Terminal atoms of the first molecule */
      xa1=x[ca1]; ya1=y[ca1]; za1=z[ca1]; 
      xa2=x[ca2]; ya2=y[ca2]; za2=z[ca2];
                                                     /* Coordinate transform */
      r1trf(npa,npb,*eta,xa,ya,za,xb,yb,zb,cmb,us);

                                                         /* Main axis vector */
      h1uvw[1]=x[ca1]-x[ca2]; h1uvw[2]=y[ca1]-y[ca2]; h1uvw[3]=z[ca1]-z[ca2];

                                               /* Generate orientation array */
      r1prr(nor); if(ier1)return;
}
