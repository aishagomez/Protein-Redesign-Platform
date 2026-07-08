/*
===============================================================================
                                                                        R1OPR.C
                                                                    GLOBAL Scan
                                                               Operating module
===============================================================================
*/
#include <stdio.h>
#include <string.h>
#include <mpi.h>

void r1inn(int,int *,char *,char *,char *,char *,char *,char *,char *,char *);
void r1inp(float *,float *,long *,int *,float *,float *,int *);
void r1usi(int *);
void r1ind(char *,int,int *);
void c1ipd(char *,char *,int,int *,int *);
void r1iov(void);
void r1pre(int,int,float *,int *,int *,long *,float *,float *,float *,float *,
           float *,float *,float *,char *,char *,int *);
void r1mla(int,int,float *,float,int *);
void r1fit(int,int,float *,float,long *,float,int,float,int *);
void r1flt(float,long,int,int *);
void r1res(char *,char *,char *,char *,char *,char *,float *,float,long,float,
           float,float,float,float,float,float,float,int,int,float,int,int,
           int *);
 
extern float x[],y[],z[],x_orig[],y_orig[],z_orig[],x_1[],y_1[],z_1[];
extern long  ggic;
extern int   maxa,npx,gic,ier1,ier2;
extern char  antip[],mmode[];
extern FILE  *fopen(),*finn,*foc,*fres,*fflog;

extern int   myProc, nProc;

void r1opr(void)
{
float ro[10];
float cmb,th,rpi,eta,eta3,xb,yb,zb,x1,y1,z1;
long  maxm,nor;
int   us[102];
int   npa,npb,l,hca,hcb,npr,npek,tri,nit,i;
char  fna[900],fnb[900],cha[50],chb[50],name_a[50],name_b[50],resn[50];
char  mf;

/*------------------------------------------------- PARAMETERS PREPROCESSING */
      gic=0; ggic=0;             /* Global counters thru all molecular pairs */
      nit=0;                                      /* Molecular pairs counter */
      tri=0;                                                          /* EOF */
/*...................... ALL COMPLEXES ONE-BY-ONE ...........................*/
      while (1)
        {
/*--------------------------------------------------------- PARAMETERS INPUT */
         r1usi(us);                                       /* User parameters */
         r1inp(ro,&th,&maxm,&npr,&rpi,&eta,us); if (ier1) return;
// parameters re-read for each complex - values change later dep on molecule
/*---------------------------------------------------------- MOLECULES INPUT */
                                            /* Read molecules filenames, etc.*/
         r1inn(nit,&tri,resn,fna,fnb,cha,chb,name_a,name_b,&mf);
         if ((ier1)||(tri==EOF))                                     /* EXIT */
           { 
            if (us[44]) { ggic/=14; fprintf(foc,"%3ld\n",ggic);} /* spec.7hel*/
            return;
           }
         if (myProc==0) fres=fopen(resn,"w");
                                                      /* Mol.A&B coord.input */
         if (mf=='r') r1ind(fnb,1,&npb); else c1ipd(fnb,chb,1,&npb,us);
         if (ier1) { ier1=0; nit++; continue; }
         if (us[34]) 
           {x1=x[us[34]];y1=y[us[34]];z1=z[us[34]];} /* Axis atom coordinates*/

         for (l=1; l<=npb; l++) {x_1[l]=x[l];y_1[l]=y[l];z_1[l]=z[l];}
         if (mf=='r') r1ind(fna,0,&npa); else c1ipd(fna,cha,0,&npa,us); 
         if (ier1) { ier1=0; nit++; continue; }
         for (l=1; l<=npa; l++) {x_orig[l]=x[l];y_orig[l]=y[l];z_orig[l]=z[l];}

         if (mmode[0]=='o') { r1iov();if(ier1)return; } /* B.site input (ovp)*/
 
/*------------------------------------------------- PARAMETERS PREPROCESSING */
         r1pre(npa,npb,&cmb,&hca,&hcb,&nor,&eta,&rpi,&xb,&yb,&zb,ro,&eta3,
               name_a,name_b,us);
         if (ier1) return; if(ier2){ ier2=0; nit++; continue; }

/*----------------------------------------------------- MOLECULES PROCESSING */

         r1mla(npa,hca,ro,eta3,us);                      /* Mol.A processing */
                                     /* Mol.B processing & fitting (Parallel)*/
         r1fit(npb,hcb,ro,eta3,&nor,cmb,npr,rpi,us); if (ier2) return; 
         MPI_Barrier(MPI_COMM_WORLD);   /* Wait of all processes to catch up */

/*-------------------------------------------------- POSTPROCESSING & OUTPUT */
         if (myProc==0)
           {
            r1flt(th,nor,npr,&npek);              /* Highest peaks treatment */
                                                                   /* Output */
            r1res(name_a,name_b,fna,fnb,cha,chb,ro,th,maxm,eta,eta3,xb,yb,zb,
               x1,y1,z1,npek,npr,rpi,npa,npb,us); fclose(fres);if(ier1)return;
           }
         nit++;
        }
}
