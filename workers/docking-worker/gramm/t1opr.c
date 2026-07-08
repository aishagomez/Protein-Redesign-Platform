/*
===============================================================================
                                                                        T1OPR.C
                                          GLOBAL Template Based Scan (TM-align)
                                                               Operating module
===============================================================================
*/
#include <stdio.h>
#include <string.h>
#include <mpi.h>

void r1inn(int,int *,char *,char *,char *,char *,char *,char *,char *,char *);
void t1inp(float *,float *,int *,int *,int *,char *);
void r1usi(int *);
void t1ind(char *,int *,int *);
void t1ali(int,int,int,int *,float,float,int,int,int *);
void c1ipd(char *,char *,int,int *,int *);
void r1srt(int);
void t1oup(int,int,int,int,char *);
void w1out(char *,char *,char *,char *,int,int *,int *,char *,char *,char *,
           char *,char *,char *,int,int,int *);
void r1us8(char *,char *,int,int,int,char *,char *);

extern float x[],y[],z[],x_1[],y_1[],z_1[],tmsa[],tmsb[],ws[];
extern long  ind[];
extern int   wgic,ier1,ier2;
extern FILE  *fok,*fflog;

extern int   myProc, nProc;    /*PRLL*/
extern MPI_Status *mpi_status; /*PRLL*/

void t1opr(void)
{
float tmscoa,tmscob;
int   npa,npb,tri,nit,covera,coverb,ntp,nt,maxmch,nmo,im,l;
int   us[102];
char  fna[900],fnb[900],cha[50],chb[50],name_a[50],name_b[50],resn[50];
char  fnn[1000],fmatch[900],sejo[50],mode[10],imol[50];
char  mf;
/*--------------------------------------------------------- PARAMETERS INPUT */

      r1usi(us);                                          /* User parameters */
      t1inp(&tmscoa,&tmscob,&covera,&coverb,&maxmch,sejo); if (ier1) return;
      imol[0]='n'; if (us[40]) imol[0]='y';

      t1ind(fnn,&ntp,us); if (ier1) return;                /* Read templates */

/*...................... ALL COMPLEXES ONE-BY-ONE ...........................*/

      wgic=0;                                  /* Counter of molecular pairs */
      nit=0;                   /* Counter of iterations to read from rmol.gr */
      tri=0;                                                          /* EOF */

      while (1)
        {
/*PRLL*/ MPI_Barrier(MPI_COMM_WORLD);  /* Wait for all processes to catch up */
                                                     /* Read molecules names */
         r1inn(nit,&tri,resn,fna,fnb,cha,chb,name_a,name_b,&mf); nit++; wgic++;
         if ((ier1)||(tri==EOF)) return;

         c1ipd(fna,cha,0,&npa,us); if (ier1) return;   /* Read mol A&B coord */
         for(l=1;l<=npa;l++) {x_1[l]=x[l];y_1[l]=y[l];z_1[l]=z[l];}
         c1ipd(fnb,chb,1,&npb,us); if (ier1) return;

         if (myProc==0)
           { fprintf(fflog,"\nComplex %3d %s-%s",wgic,name_a,name_b);
             if (nProc==1) fprintf(fflog,"  TM-score  coverage");
             if (us[2]) { fflush (stdout); 
                          printf("\nComplex %3d %s-%s",wgic,name_a,name_b);
                          if((us[2]==2)&&(nProc==1)) { fflush (stdout);
                              printf("  TM-score  coverage"); printf("\n"); }}}

/*---------------------------------------------------------------- ALIGNMENT */

         t1ali(npa,npb,ntp,&nt,tmscoa,tmscob,covera,coverb,us);
         if(myProc==0)
           {
            if (ier2) { ier2=0; continue; }          /* No templates for A&B */
            for (im=1; im<=nt; im++)      /* SORT matches according to score */
              { ws[im]=-(tmsa[im]+tmsb[im]);     /* Rank by sum of TM-scores */
                ind[im]=im; }
            if (nt>1) r1srt(nt);     /* asc order of negatives => decs order */

/*----------------------------------------- MOLECULES IN PREDICTED POSITIONS */

            nmo=maxmch; if (nmo>nt) nmo=nt;
            t1oup(nmo,nt,npa,npb,sejo);

/*------------------------------------------------------------------- OUTPUT */
            strcpy(mode,"tbased");

            if (us[48]){r1us8(mode,sejo,nmo,npa,npb,name_a,name_b); continue; }

            strcpy(fmatch,name_a); strcat(fmatch,"-");
            strcat(fmatch,name_b); strcat(fmatch,".res");/*fake .res filename*/

            w1out(mode,fmatch,sejo,imol,nmo,0,0,name_a,name_b,fna,fnb,cha,chb,
                  npa,npb,us);
           }
        }
/*PL*/MPI_Barrier(MPI_COMM_WORLD);     /* Wait for all processes to catch up */
      fclose(fok); fclose(fflog);
}
