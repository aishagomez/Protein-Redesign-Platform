/*
===============================================================================
                                                                        W1OPR.C
                                                               LOCALt Refinement
                                                               Operating module
===============================================================================
*/
#include <stdio.h>
#include <string.h>
#include <mpi.h>
#include "r1dim.h"
#include "w1dim.h"

void r1usi(int *);
void w1inp(int *,int *,int *,int *,int *,float *,int *,int *,char *);
void w1inn(int,int *,char *);
void w1irs(char *,int,int,char *,char *,int *,char *,char *,char *,char *,
           char *,char *,int *,int *,float *,float *,float *,int *);
void cninr(char *,int *,int *,int *,int *);
void r1rah(int,int,float *);
void w1crd(int,int,int,int,float *,float *,float *,float *,float,float,float,
           int *);
void w1sco(int,int,int,int,int,int *,int *,int,int,int,int *);
void w1rr1(void);
void w1rr2(void);
void w1clu(int,int,int,float,int *,int *);
void w1bak(int,int,int,int,int *,int *,int *);
void w1out(char *,char *,char *,char *,int,int *,int *,char *,char *,char *,
           char *,char *,char *,int,int,int *);
void r1srt(int);
//void r1us7(int,int,int,char *,char *,float,float,float,float *,float *,
//           float *,float *,float *,float *,int *);
void r1us8(char *,char *,int,int,int,char *,char *);

extern float x_1[],y_1[],z_1[];
extern float xko[][DIM1+1],yko[][DIM1+1],zko[][DIM1+1];
extern float xao[][DIM1+1],yao[][DIM1+1],zao[][DIM1+1];
extern float xw [][DIM1+1],yw [][DIM1+1],zw [][DIM1+1];
extern float xaw[][DIM1+1],yaw[][DIM1+1],zaw[][DIM1+1];
extern float lxko[],lyko[],lzko[],lxao[],lyao[],lzao[];
extern float xk[],yk[],zk[];
extern float cmao[][4],cmbo[][4],cmbbo[][4],cmo[][4],ws[];
extern float al[],bl[],gl[],ul[],vl[],wl[];
extern long  ind[];
extern int   energy[],wgic,ier1,ier2;
extern FILE  *fok;

extern int   myProc, nProc;    /*PRLL*/
extern MPI_Status *mpi_status; /*PRLL*/

void w1opr(void)
{
float cma[5],cmb[5],cmbb[5],cm[5];
float rclusl,rclusll,ai,bi,gi,dum;
int   energyo[DIMF+2];
int   clusl[DIMF+2],cluslo[DIMF+2],us[102];
int   conresa[DIM11+2],conresb[DIM11+2];
int   i,j,im,imo,tri,nit,mtch_f,mtch_l,maxmch,scovdw,scosta,mbak,nm,nmo,npa,
      npb,cnew;
int   imd,ic,ctr,conwei_p,conwei_n;
int   beg,end,block,ipc,ibeg,iblock; /*PRLL*/
char  fmatch[900],sejo[50],imol[50],name_a[900],name_b[900],fna[900],fnb[900];
char  cha[50],chb[50],mode[10];

/*--------------------------------------------------------- PARAMETERS INPUT */

      r1usi(us);                                          /* User parameters */
      if (us[2]&&(myProc==0)) { fflush (stdout); printf("\nREFINEMENT"); }
      w1inp(&mtch_f,&mtch_l,&scovdw,&scosta,&ctr,&rclusl,&mbak,&maxmch,sejo);
      if (ier1) return;
      imol[0]='n'; if (us[40]) imol[0]='y';

/*------------------------------------------------- PARAMETERS PREPROCESSING */

      wgic=0;                                  /* Counter of molecular pairs */
      nit=0;                  /* Counter of iterations to read from wlist.gr */
      tri=0;                                                          /* EOF */
      rclusll=rclusl*rclusl;

      if (scosta==1) w1rr1();            /* Initiate res-res potential table */
      if (scosta==2) w1rr2();

/*...................... ALL COMPLEXES ONE-BY-ONE ...........................*/

      while (1)
        {
/*---------------------------------------------------------- MOLECULES INPUT */
         w1inn(nit,&tri,fmatch); nit++;                     /* Read RES name */
         if (ier1||(tri==EOF)) return;             /* EXIT no more RES files */
                                                            /* Read RES file */
         w1irs(fmatch,mtch_f,mtch_l,sejo,imol,&nm,name_a,name_b,fna,fnb,
               cha,chb,&npa,&npb,&ai,&bi,&gi,us);
         if (ier1) return;
         if (ier2) { ier2=0; continue; }       /* Empty RES (no [molecules]) */
/*---------------------------------------------------------------------------*/
                         /* Build valent structure for conformational search */
/*csseq()*/ /*Depends on approach to flex docking ... to be determined later */
/*cssrv()*/
         r1rah(npa,npb,&dum);/* 'temporary' rigid only: atom radii assignment*/

/*---------------------------------------------------------------------------*/

         if(us[2]&&(myProc==0))
           { fflush (stdout); printf("\nComplex %3d %s-%s",nit,name_a,name_b);}

/*-------------------------------------------------------- CONSTRAINTS INPUT */
         if (us[2]&&(ctr==0)&&(myProc==0)) 
           { printf("\nNo constrs %s  No constrs %s",name_a,name_b); }
         if (ctr)
           {
            for (i=1; i<=DIM11; i++) { conresa[i]=0; conresb[i]=0; }
            cninr(name_a,conresa,&conwei_p,&conwei_n,&tri); if (ier1) return;
            if(us[2]&&(tri==EOF)&&(myProc==0))printf("\nNo constrs %s",name_a);
            tri=1;
            cninr(name_b,conresb,&conwei_p,&conwei_n,&tri);
            if(us[2]&&(tri==EOF)&&(myProc==0))printf("  No constrs %s",name_b);
            tri=1;
           }
/*-------------------------------------------------------------------------- */
                    /* Eval.Criterion 2, low-res distrib (supress PDB output)*/
//       if (us[47]) { r1us7(npa,npb,nm,name_a,name_b,ai,bi,gi,al,bl,gl,
//                           ul,vl,wl,us); continue; }

         nmo=1;                                         /* No.of matches out */
         cnew=1;                                /* Cluster new 1, existing 0 */
         for (i=1; i<=maxmch; i++) clusl[i]=1; /* Initial clusters occupancy */
         for (im=1; im<=nm; im++) ind[im]=im;           /* Index for sorting */

/*....................... ALL MATCHES ONE-BY-ONE ............................*/

/*----------------------------------------------------------- SCORING LO-RES */

/* Generate coordinates and score matches one-by-one, re-sort without coord,
   recycle xk,yk,zk (too much memory if accumulate) */

         if (scovdw||scosta||ctr)
           {
            if ((us[2]>1)&&(myProc==0))
              { fflush (stdout); printf("\nScore   ...      "); }

/*PRLL*/ /* Block decomposition of matches */
            block = nm / nProc;
            beg = myProc * block + 1;
            end = (myProc + 1) * block;  if(myProc == nProc - 1) end = nm;
            ic=0;                         /* Energies counter (for PARALLEL) */
            for (im=beg; im<=end; im++)
              {                          /* Generate coordinates for scoring */
               w1crd(im,ic,npa,npb,cma,cmb,cmbb,cm,ai,bi,gi,us); 
               if(ier1) return;
               w1sco(scovdw,scosta,ctr,npa,npb,conresa,conresb,
                     conwei_p,conwei_n,beg,&ic);
               if ((us[2]>1)&&(nProc==1)) printf("\b\b\b\b\b%5d",im);
              }
/*PRLL*/ /* send number of energies and energies arrays to share */
            if(myProc != 0)
              {
               MPI_Send(&ic, 1, MPI_INT, 0, 1, MPI_COMM_WORLD); 
               MPI_Send(&energy[1], ic, MPI_INT, 0, 1, MPI_COMM_WORLD);
              }
            else if(nProc > 1)/*proc 0 get count to iblock & ener to own ener*/
              {
               ibeg = ic + 1; /*start after proc 0 energizes: root is worker */
               for(ipc=1; ipc < nProc; ipc++)
                 {
                  MPI_Recv(&iblock,1,MPI_INT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
                  MPI_Recv(&energy[ibeg],iblock,MPI_INT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
                  ibeg = ibeg + iblock; 
                 }
              }
/*PRLL*/    MPI_Barrier(MPI_COMM_WORLD);/* Wait for all processes to catch up*/

            if(myProc==0)
              {                              /* Sort according to new energy */
               for (im=1; im<=nm; im++) ws[im]=(float)(-energy[im]);
               r1srt(nm);                                       /* asc order */
               for (im=1; im<=nm; im++) energy[im]=(int)(-ws[im]);/*dsc order*/
              }
           }
//printf("\nenergy[1]=%d energy[10]=%d",energy[1],energy[10]);
/*-------------------------------------------------------------------------- */
         if(myProc==0)
           {
            for (im=1; im<=nm; im++)
              {                                /* Generate coordinates again */
               w1crd(im,-1,npa,npb,cma,cmb,cmbb,cm,ai,bi,gi,us); 
               if(ier1) return;

               if (im==1)                          /* Accumulate first match */
                 {
                  for (i=1; i<=npb; i++)
                    {xko[nmo][i]=xk[i]; yko[nmo][i]=yk[i]; zko[nmo][i]=zk[i]; }
                  for (i=1; i<=npa; i++)
                    {xao[nmo][i]=x_1[i];yao[nmo][i]=y_1[i];zao[nmo][i]=z_1[i];}
                  for(j=1;j<=3; j++){cmao[nmo][j]=cma[j];cmbo[nmo][j]=cmb[j];
                                     cmbbo[nmo][j]=cmbb[j]; cmo[nmo][j]=cm[j];}
                  energyo[nmo]=energy[im];
                 }
/*----------------------------------------------------------- CLUSTER LO-RES */
               if (rclusl)
                 {
                  w1clu(im,nmo,npb,rclusll,clusl,&cnew);
                  if (cnew==0) continue;
                 }
/*-------------------------------------------------------------------------- */
               if (im>1)                               /* Accumulate matches */
                 {
                  nmo++; if (nmo>maxmch) { nmo--; break; }
                  for (i=1; i<=npb; i++)
                    {xko[nmo][i]=xk[i]; yko[nmo][i]=yk[i]; zko[nmo][i]=zk[i]; }
                  for (i=1; i<=npa; i++)
                    {xao[nmo][i]=x_1[i];yao[nmo][i]=y_1[i];zao[nmo][i]=z_1[i];}
                  for(j=1; j<=3; j++){cmao[nmo][j]=cma[j]; cmbo[nmo][j]=cmb[j];
                                     cmbbo[nmo][j]=cmbb[j]; cmo[nmo][j]=cm[j];}
                  energyo[nmo]=energy[im];
                 }
              }
           }
/*------------------------------------------------------------- MINIMIZATION */
         if (mbak)
           {
            if(myProc == 0)
              {
               if(us[2]) { fflush (stdout); printf("\nMinimize...      "); }
                                  /* Send everything from 0 proc to all proc */
               for (imo=1; imo<=nmo; imo++)           /* Pack arrays to send */
                 { for (i=1; i<=npb; i++)
                    { lxko[(long)((imo-1)*npb+i)]=xko[imo][i];
                      lyko[(long)((imo-1)*npb+i)]=yko[imo][i];
                      lzko[(long)((imo-1)*npb+i)]=zko[imo][i]; }
                  for (i=1; i<=npa; i++)
                    { lxao[(long)((imo-1)*npa+i)]=xao[imo][i];
                      lyao[(long)((imo-1)*npa+i)]=yao[imo][i];
                      lzao[(long)((imo-1)*npa+i)]=zao[imo][i]; } }

               for(ipc=1; ipc < nProc; ipc++)
                 {
                  MPI_Send(&nmo,       1,      MPI_INT,  ipc,1,MPI_COMM_WORLD);
                  MPI_Send(&energyo[1],nmo,    MPI_INT,  ipc,1,MPI_COMM_WORLD);
                  MPI_Send(&lxko[1l],  nmo*npb,MPI_FLOAT,ipc,1,MPI_COMM_WORLD);
                  MPI_Send(&lyko[1l],  nmo*npb,MPI_FLOAT,ipc,1,MPI_COMM_WORLD);
                  MPI_Send(&lzko[1l],  nmo*npb,MPI_FLOAT,ipc,1,MPI_COMM_WORLD);
                  MPI_Send(&lxao[1l],  nmo*npa,MPI_FLOAT,ipc,1,MPI_COMM_WORLD);
                  MPI_Send(&lyao[1l],  nmo*npa,MPI_FLOAT,ipc,1,MPI_COMM_WORLD);
                  MPI_Send(&lzao[1l],  nmo*npa,MPI_FLOAT,ipc,1,MPI_COMM_WORLD);
                 }
              }
            else if(nProc > 1)
              {
               MPI_Recv(&nmo,       1,      MPI_INT,  0,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
               MPI_Recv(&energyo[1],nmo,    MPI_INT,  0,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
               MPI_Recv(&lxko[1l],  nmo*npb,MPI_FLOAT,0,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
               MPI_Recv(&lyko[1l],  nmo*npb,MPI_FLOAT,0,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
               MPI_Recv(&lzko[1l],  nmo*npb,MPI_FLOAT,0,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
               MPI_Recv(&lxao[1l],  nmo*npa,MPI_FLOAT,0,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
               MPI_Recv(&lyao[1l],  nmo*npa,MPI_FLOAT,0,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
               MPI_Recv(&lzao[1l],  nmo*npa,MPI_FLOAT,0,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);

               for (imo=1; imo<=nmo; imo++)
                 { for (i=1; i<=npb; i++)
                    { xko[imo][i]=lxko[(long)((imo-1)*npb+i)];
                      yko[imo][i]=lyko[(long)((imo-1)*npb+i)];
                      zko[imo][i]=lzko[(long)((imo-1)*npb+i)]; }
                  for (i=1; i<=npa; i++)
                    { xao[imo][i]=lxao[(long)((imo-1)*npa+i)];
                      yao[imo][i]=lyao[(long)((imo-1)*npa+i)];
                      zao[imo][i]=lzao[(long)((imo-1)*npa+i)]; } }
              }
/*PRLL*/    MPI_Barrier(MPI_COMM_WORLD);/* Wait for all processes to catch up*/
                                                          /* Distribute load */
/*PRLL*/    block = nmo / nProc;           /* Block decomposition of matches */
            beg = myProc * block + 1;
            end = (myProc + 1) * block;  if(myProc == nProc - 1) end = nmo;
            ic=0;                                        /* Energies counter */
            for (imo=beg; imo<=end; imo++)
              {
               w1bak(mbak,imo,npa,npb,energyo,&ic,us);       /* >>>>>>>>>>>> */
              }
            if(myProc != 0)                /* Send everything back to 0 proc */
              {
               for (imo=1; imo<=ic; imo++)
                 { for (i=1; i<=npb; i++)
                    { lxko[(long)((imo-1)*npb+i)]=xko[imo][i];
                      lyko[(long)((imo-1)*npb+i)]=yko[imo][i];
                      lzko[(long)((imo-1)*npb+i)]=zko[imo][i]; }
                  for (i=1; i<=npa; i++)
                    { lxao[(long)((imo-1)*npa+i)]=xao[imo][i];
                      lyao[(long)((imo-1)*npa+i)]=yao[imo][i];
                      lzao[(long)((imo-1)*npa+i)]=zao[imo][i]; } }

               MPI_Send(&ic,        1,     MPI_INT,  0,1,MPI_COMM_WORLD);   
               MPI_Send(&energyo[1],ic,    MPI_INT,  0,1,MPI_COMM_WORLD);
               MPI_Send(&lxko[1l],  ic*npb,MPI_FLOAT,0,1,MPI_COMM_WORLD);
               MPI_Send(&lyko[1l],  ic*npb,MPI_FLOAT,0,1,MPI_COMM_WORLD);
               MPI_Send(&lzko[1l],  ic*npb,MPI_FLOAT,0,1,MPI_COMM_WORLD);
               MPI_Send(&lxao[1l],  ic*npa,MPI_FLOAT,0,1,MPI_COMM_WORLD);
               MPI_Send(&lyao[1l],  ic*npa,MPI_FLOAT,0,1,MPI_COMM_WORLD);
               MPI_Send(&lzao[1l],  ic*npa,MPI_FLOAT,0,1,MPI_COMM_WORLD);
              }
            else if(nProc > 1)/*proc0 get count to iblock &array to own array*/
              {
               ibeg = ic + 1; /*start after proc 0 energizes: root is worker */
               for(ipc=1; ipc < nProc; ipc++)
                 {
                  MPI_Recv(&iblock,                      1,         MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
                  MPI_Recv(&energyo[ibeg],               iblock,    MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
                  MPI_Recv(&lxko[(long)((ibeg-1)*npb+1)],iblock*npb,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
                  MPI_Recv(&lyko[(long)((ibeg-1)*npb+1)],iblock*npb,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
                  MPI_Recv(&lzko[(long)((ibeg-1)*npb+1)],iblock*npb,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
                  MPI_Recv(&lxao[(long)((ibeg-1)*npa+1)],iblock*npa,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
                  MPI_Recv(&lyao[(long)((ibeg-1)*npa+1)],iblock*npa,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
                  MPI_Recv(&lzao[(long)((ibeg-1)*npa+1)],iblock*npa,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);

                  for (imo=ibeg; imo<=(ibeg+iblock); imo++)
                    { for (i=1; i<=npb; i++)
                       { xko[imo][i]=lxko[(long)((imo-1)*npb+i)];
                         yko[imo][i]=lyko[(long)((imo-1)*npb+i)];
                         zko[imo][i]=lzko[(long)((imo-1)*npb+i)]; }
                     for (i=1; i<=npa; i++)
                       { xao[imo][i]=lxao[(long)((imo-1)*npa+i)];
                         yao[imo][i]=lyao[(long)((imo-1)*npa+i)];
                         zao[imo][i]=lzao[(long)((imo-1)*npa+i)]; } }

                  ibeg = ibeg + iblock;
                 }
              }
/*PRLL*/    MPI_Barrier(MPI_COMM_WORLD);/* Wait of all processes to catch up */

            if(myProc==0)
              {                              /* SORT according to new energy */
               if (nmo>1)
                 {
                  for (imo=1; imo<=nmo; imo++) 
                    { ws[imo]=(float)(-energyo[imo]); ind[imo]=imo; }
                  r1srt(nmo);                                   /* asc order */
                  for (imo=1; imo<=nmo; imo++)
                    { energyo[imo]=(int)(-ws[imo]);            /* desc order */
                      for (i=1; i<=npb; i++){xw[imo][i]=xko[imo][i];/*->work */
                                             yw[imo][i]=yko[imo][i];
                                             zw[imo][i]=zko[imo][i]; }
                      for (i=1; i<=npa; i++){xaw[imo][i]=xao[imo][i];
                                             yaw[imo][i]=yao[imo][i];
                                             zaw[imo][i]=zao[imo][i]; }
/*** re-sort CMAO ? */
                    }
                  for (imo=1; imo<=nmo; imo++)
                    { imd=ind[imo];
                      cluslo[imo]=clusl[imd]; /* re-sorted cluster occupancy */
                      for (i=1; i<=npb; i++){xko[imo][i]=xw[imd][i];/*<-work */
                                             yko[imo][i]=yw[imd][i];
                                             zko[imo][i]=zw[imd][i]; }
                      for (i=1; i<=npa; i++){xao[imo][i]=xaw[imd][i];
                                             yao[imo][i]=yaw[imd][i];
                                             zao[imo][i]=zaw[imd][i]; } 
/*** re-sort CMO ? */
                    } 
                 }
              }
           }
/*----------------------------------------------------------- SCORING HI-RES */


/*----------------------------------------------------------- CLUSTER HI-RES */


/* ------------------------------------------------------------------ OUTPUT */
         if(myProc==0)
           {              /* Eval. Criterion 3, CAPRI-like (supress PDB out) */
            strcpy(mode,"free");

            if (us[48]) { r1us8(mode,sejo,nmo,npa,npb,name_a,name_b);continue;}

            if((mbak==0)||(nmo==1))   /* cluster occupancy was not re-sorted */
              { for (imo=1; imo<=nmo; imo++) { cluslo[imo]=clusl[imo];}}
            w1out(mode,fmatch,sejo,imol,nmo,energyo,cluslo,name_a,name_b,
                  fna,fnb,cha,chb,npa,npb,us);
           }
        }
      fclose(fok);
}
