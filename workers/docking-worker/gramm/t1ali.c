/*
===============================================================================
                                                                        T1ALI.C
                                           Structure alignment to all templates
===============================================================================
*/
#include <stdio.h>
#include <string.h>
#include <mpi.h>
#include "r1dim.h"

void rrcalls_(void);                          /* declare TM-align subroutine */
                                       /*define struct to sync with TM-align */
extern struct { int nseq1,nseq2;} length_;                    /* seq lengths */
extern struct {
int   n8_al;                                               /* aligned length */
float rmsd8_al,TMS,seq_id;                   /* rmsd, TM-score, seq identity */
float TR[3];                                                  /* translation */
float UR[9]; } ram_;                                             /* rotation */
                 /* If DIMM11 is increased - increase also in Fortran (nmax) */
extern struct { char  ss1[DIM11][3],ss2[DIM11][3];} sequ_;      /* sequences */
extern struct { int   mm1[DIM11],mm2[DIM11]; } initial4_; /* residues number */
extern struct { float xtrg[DIM11],ytrg[DIM11],ztrg[DIM11];}trg_;/*coord targt*/
extern struct { float xtpl[DIM11],ytpl[DIM11],ztpl[DIM11];}tpl_;/*coord tmplt*/

extern float rmsda[],rmsdb[],tmsa[],tmsb[];
extern float x[],y[],z[],x_1[],y_1[],z_1[],xca[][2],yca[][2],zca[][2];
extern float xtp[][DIM11][2],ytp[][DIM11][2],ztp[][DIM11][2];
extern float tra[][4],trb[][4],ura[][10],urb[][10];
extern float ltra[],ltrb[],lura[],lurb[];                              /*PRLL*/
extern int   seqa[],seqb[],cova[],covb[],rnber[][2],rrnber[][2],nrt[][2];
extern int   trnum[][DIM11][2],ier2;
extern char  tna[][20],tnb[][20],tnam[][20],resnam[][2][4],rresnam[][2][3];
extern char  ltna[],ltnb[];                                            /*PRLL*/
extern char  trnam[][DIM11][2][3],atmnam[][2][4];
extern FILE  *fflog;

extern int   myProc, nProc;                                            /*PRLL*/
extern MPI_Status *mpi_status;                                         /*PRLL*/

void t1ali(int npa,int npb,int ntp,int *nnt,float tmscoa,float tmscob,
           int covera,int coverb,int *us)
{
int   npr[2],np,nt,itp,ntp2,i12,nseq,i,ii,j,l,m;
int   beg,end,block,ipc,ibeg,iend;                                     /*PRLL*/

      ntp2=ntp*2;  /* total no.matches for 1-2 on 1-2 and 1-2 on 2-1 algnmnt */
      for (m=0; m<=1; m++)                    /* CA coordinates of Mol A & B */
        {
         ii=0;
         if (m==0) np=npa; else np=npb;
         for (l=1; l<=np; l++)
           {
            if (strncmp(atmnam[l][m]," CA ",4)!=0) continue;
            ii++;
            if (m==0) { xca[ii][m]=x_1[l];yca[ii][m]=y_1[l];zca[ii][m]=z_1[l];}
            else      { xca[ii][m]=x[l];  yca[ii][m]=y[l];  zca[ii][m]=z[l];  }
            rrnber[ii][m]=rnber[l][m];
            for (j=0; j<=2; j++) rresnam[ii][m][j]=resnam[l][m][j+1];
           }
         npr[m]=ii;
        }
                                                          /* Distribute load */
/*PL*/block = ntp / nProc;               /* Block decomposition of templates */
      beg = myProc * block + 1;
      end = (myProc + 1) * block;  if(myProc == nProc - 1) end = ntp;

      for (i12=1; i12<=2; i12++)      /* Align 1-2 with 1-2 and 1-2 with 2-1 */
        {
         if (us[2]&&(i12==1)&&(nProc==1)) printf("  template ");

         for (i=beg; i<=end; i++)
           {
            if ((us[2])&&(nProc==1)) printf("%4d\b\b\b\b",i);
            itp=i+ntp*(i12-1);
/*------------------------------------------------------------------ Align A */

            length_.nseq1=npr[0];                                  /* target */
            for (ii=1; ii<=npr[0]; ii++)
              {
               for (j=0; j<=2; j++) sequ_.ss1[ii-1][j]=rresnam[ii][0][j];
               initial4_.mm1[ii-1]=rrnber[ii][0];
               trg_.xtrg[ii-1]=xca[ii][0];
               trg_.ytrg[ii-1]=yca[ii][0];
               trg_.ztrg[ii-1]=zca[ii][0];
              }
            length_.nseq2=nrt[i][i12-1];                         /* template */
            for (ii=1; ii<=nrt[i][i12-1]; ii++)
              {
               for (j=0; j<=2; j++) sequ_.ss2[ii-1][j]=trnam[i][ii][i12-1][j];
               initial4_.mm2[ii-1]=trnum[i][ii][i12-1];
               tpl_.xtpl[ii-1]=xtp[i][ii][i12-1];
               tpl_.ytpl[ii-1]=ytp[i][ii][i12-1];
               tpl_.ztpl[ii-1]=ztp[i][ii][i12-1];
              }
            rrcalls_();                                     /* >>>> TM-align */

            rmsda[itp]=ram_.rmsd8_al; tmsa[itp]=ram_.TMS;
            seqa[itp]=100*ram_.seq_id; nseq=length_.nseq1; 
            if (length_.nseq2 < length_.nseq1) nseq=length_.nseq2;
            cova[itp]=(int)(100.*(float)ram_.n8_al/(float)nseq);

            strcpy(tna[itp],tnam[i]); 
            if (i12==1) strcat(tna[itp],"_1");  else strcat(tna[itp],"_2");
            for (j=1; j<=3; j++) tra[itp][j]=ram_.TR[j-1];
            for (j=1; j<=9; j++) ura[itp][j]=ram_.UR[j-1];

/*------------------------------------------------------------------ Align B */

            length_.nseq1=npr[1];                                  /* target */
            for (ii=1; ii<=npr[1]; ii++)
              {
               for (j=0; j<=2; j++) sequ_.ss1[ii-1][j]=rresnam [ii][1][j];
               initial4_.mm1[ii-1]=rrnber[ii][1];
               trg_.xtrg[ii-1]=xca[ii][1];
               trg_.ytrg[ii-1]=yca[ii][1];
               trg_.ztrg[ii-1]=zca[ii][1];
              }
            length_.nseq2=nrt[i][2-i12];                         /* template */
            for (ii=1; ii<=nrt[i][2-i12]; ii++)
              {
               for (j=0; j<=2; j++) sequ_.ss2[ii-1][j]=trnam[i][ii][2-i12][j];
               initial4_.mm2[ii-1]=trnum[i][ii][2-i12];
               tpl_.xtpl[ii-1]=xtp[i][ii][2-i12];
               tpl_.ytpl[ii-1]=ytp[i][ii][2-i12];
               tpl_.ztpl[ii-1]=ztp[i][ii][2-i12];
              }
            rrcalls_();                                     /* >>>> TM-align */

            rmsdb[itp]=ram_.rmsd8_al; tmsb[itp]=ram_.TMS; 
            seqb[itp]=100*ram_.seq_id; nseq=length_.nseq1; 
            if (length_.nseq2 < length_.nseq1) nseq=length_.nseq2;
            covb[itp]=(int)(100.*(float)ram_.n8_al/(float)nseq);

            strcpy(tnb[itp],tnam[i]); 
            if (i12==1) strcat(tnb[itp],"_2");  else strcat(tnb[itp],"_1");
            for (j=1; j<=3; j++) trb[itp][j]=ram_.TR[j-1];
            for (j=1; j<=9; j++) urb[itp][j]=ram_.UR[j-1];
           }
        }
/*PL*/MPI_Barrier(MPI_COMM_WORLD);     /* Wait for all processes to catch up */
      if(myProc != 0)                      /* Send everything back to 0 proc */
        {
         for (i=beg; i<=end; i++)                     /* Pack arrays to send */
           { for (j=0; j<20; j++)
               { ltna[(long)((i-1)*20+j)]=tna[i][j]; ltna[(long)((i+ntp-1)*20+j)]=tna[i+ntp][j];
                 ltnb[(long)((i-1)*20+j)]=tnb[i][j]; ltnb[(long)((i+ntp-1)*20+j)]=tnb[i+ntp][j];   }
             for (j=0; j<3; j++)
               { ltra[(long)((i-1)*3+j)]=tra[i][j+1]; ltra[(long)((i+ntp-1)*3+j)]=tra[i+ntp][j+1];
                 ltrb[(long)((i-1)*3+j)]=trb[i][j+1]; ltrb[(long)((i+ntp-1)*3+j)]=trb[i+ntp][j+1]; }
             for (j=0; j<9; j++)
               { lura[(long)((i-1)*9+j)]=ura[i][j+1]; lura[(long)((i+ntp-1)*9+j)]=ura[i+ntp][j+1];
                 lurb[(long)((i-1)*9+j)]=urb[i][j+1]; lurb[(long)((i+ntp-1)*9+j)]=urb[i+ntp][j+1]; }}
         MPI_Send(&rmsda[beg],    end+1-beg,MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&rmsda[beg+ntp],end+1-beg,MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&rmsdb[beg],    end+1-beg,MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&rmsdb[beg+ntp],end+1-beg,MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&tmsa [beg],    end+1-beg,MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&tmsa [beg+ntp],end+1-beg,MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&tmsb [beg],    end+1-beg,MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&tmsb [beg+ntp],end+1-beg,MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&seqa [beg],    end+1-beg,MPI_INT,  0,1,MPI_COMM_WORLD);
         MPI_Send(&seqa [beg+ntp],end+1-beg,MPI_INT,  0,1,MPI_COMM_WORLD);
         MPI_Send(&seqb [beg],    end+1-beg,MPI_INT,  0,1,MPI_COMM_WORLD);
         MPI_Send(&seqb [beg+ntp],end+1-beg,MPI_INT,  0,1,MPI_COMM_WORLD);
         MPI_Send(&cova [beg],    end+1-beg,MPI_INT,  0,1,MPI_COMM_WORLD);
         MPI_Send(&cova [beg+ntp],end+1-beg,MPI_INT,  0,1,MPI_COMM_WORLD);
         MPI_Send(&covb [beg],    end+1-beg,MPI_INT,  0,1,MPI_COMM_WORLD);
         MPI_Send(&covb [beg+ntp],end+1-beg,MPI_INT,  0,1,MPI_COMM_WORLD);
         MPI_Send(&ltna[(long)((beg-1)*20)],    (long)((end+1-beg)*20),MPI_CHAR,0,1,MPI_COMM_WORLD);
         MPI_Send(&ltna[(long)((beg+ntp-1)*20)],(long)((end+1-beg)*20),MPI_CHAR,0,1,MPI_COMM_WORLD);
         MPI_Send(&ltnb[(long)((beg-1)*20)],    (long)((end+1-beg)*20),MPI_CHAR,0,1,MPI_COMM_WORLD);
         MPI_Send(&ltnb[(long)((beg+ntp-1)*20)],(long)((end+1-beg)*20),MPI_CHAR,0,1,MPI_COMM_WORLD);
         MPI_Send(&ltra[(long)((beg-1)*3)],     (long)((end+1-beg)*3),MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&ltra[(long)((beg+ntp-1)*3)], (long)((end+1-beg)*3),MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&ltrb[(long)((beg-1)*3)],     (long)((end+1-beg)*3),MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&ltrb[(long)((beg+ntp-1)*3)], (long)((end+1-beg)*3),MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&lura[(long)((beg-1)*9)],     (long)((end+1-beg)*9),MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&lura[(long)((beg+ntp-1)*9)], (long)((end+1-beg)*9),MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&lurb[(long)((beg-1)*9)],     (long)((end+1-beg)*9),MPI_FLOAT,0,1,MPI_COMM_WORLD);
         MPI_Send(&lurb[(long)((beg+ntp-1)*9)], (long)((end+1-beg)*9),MPI_FLOAT,0,1,MPI_COMM_WORLD);
        }
      else if(nProc > 1)
        {
         for(ipc=1; ipc < nProc; ipc++)
           {
            ibeg=ipc*block+1; iend=(ipc+1)*block; if(ipc==(nProc-1)) iend=ntp;

            MPI_Recv(&rmsda[ibeg],    iend+1-ibeg,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&rmsda[ibeg+ntp],iend+1-ibeg,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&rmsdb[ibeg],    iend+1-ibeg,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&rmsdb[ibeg+ntp],iend+1-ibeg,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&tmsa [ibeg],    iend+1-ibeg,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&tmsa [ibeg+ntp],iend+1-ibeg,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&tmsb [ibeg],    iend+1-ibeg,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&tmsb [ibeg+ntp],iend+1-ibeg,MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&seqa [ibeg],    iend+1-ibeg,MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&seqa [ibeg+ntp],iend+1-ibeg,MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&seqb [ibeg],    iend+1-ibeg,MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&seqb [ibeg+ntp],iend+1-ibeg,MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&cova [ibeg],    iend+1-ibeg,MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&cova [ibeg+ntp],iend+1-ibeg,MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&covb [ibeg],    iend+1-ibeg,MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&covb [ibeg+ntp],iend+1-ibeg,MPI_INT,  ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&ltna[(long)((ibeg-1)*20)],    (long)((iend+1-ibeg)*20),MPI_CHAR,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&ltna[(long)((ibeg+ntp-1)*20)],(long)((iend+1-ibeg)*20),MPI_CHAR,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&ltnb[(long)((ibeg-1)*20)],    (long)((iend+1-ibeg)*20),MPI_CHAR,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&ltnb[(long)((ibeg+ntp-1)*20)],(long)((iend+1-ibeg)*20),MPI_CHAR,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&ltra[(long)((ibeg-1)*3)],     (long)((iend+1-ibeg)*3),MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&ltra[(long)((ibeg+ntp-1)*3)], (long)((iend+1-ibeg)*3),MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&ltrb[(long)((ibeg-1)*3)],     (long)((iend+1-ibeg)*3),MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&ltrb[(long)((ibeg+ntp-1)*3)], (long)((iend+1-ibeg)*3),MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&lura[(long)((ibeg-1)*9)],     (long)((iend+1-ibeg)*9),MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&lura[(long)((ibeg+ntp-1)*9)], (long)((iend+1-ibeg)*9),MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&lurb[(long)((ibeg-1)*9)],     (long)((iend+1-ibeg)*9),MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&lurb[(long)((ibeg+ntp-1)*9)], (long)((iend+1-ibeg)*9),MPI_FLOAT,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);

            for (i=ibeg; i<=iend; i++)             /* Unpack received arrays */
              { for (j=0; j<20; j++)
                  { tna[i][j]=ltna[(long)((i-1)*20+j)]; tna[i+ntp][j]=ltna[(long)((i+ntp-1)*20+j)];
                    tnb[i][j]=ltnb[(long)((i-1)*20+j)]; tnb[i+ntp][j]=ltnb[(long)((i+ntp-1)*20+j)];   }
                for (j=0; j<3; j++)
                  { tra[i][j+1]=ltra[(long)((i-1)*3+j)]; tra[i+ntp][j+1]=ltra[(long)((i+ntp-1)*3+j)];
                    trb[i][j+1]=ltrb[(long)((i-1)*3+j)]; trb[i+ntp][j+1]=ltrb[(long)((i+ntp-1)*3+j)]; }
                for (j=0; j<9; j++)
                  { ura[i][j+1]=lura[(long)((i-1)*9+j)]; ura[i+ntp][j+1]=lura[(long)((i+ntp-1)*9+j)];
                    urb[i][j+1]=lurb[(long)((i-1)*9+j)]; urb[i+ntp][j+1]=lurb[(long)((i+ntp-1)*9+j)]; }}
           }
        }
/*PL*/MPI_Barrier(MPI_COMM_WORLD);     /* Wait for all processes to catch up */
/*-------------------------------------------------- Eliminate bad templates */
      if(myProc==0)
        {
         nt=0;
         for (i=1; i<=ntp2; i++)
           {
            if ((tmsa[i]<tmscoa)||(tmsb[i]<tmscob)||
                (cova[i]<covera)||(covb[i]<coverb)) continue;
            nt++;
            rmsda[nt]=rmsda[i]; rmsdb[nt]=rmsdb[i];
            tmsa [nt]=tmsa [i]; tmsb [nt]=tmsb [i];
            seqa [nt]=seqa [i]; seqb [nt]=seqb [i];
            cova [nt]=cova [i]; covb [nt]=covb [i];
            strcpy(tna[nt],tna[i]); strcpy(tnb[nt],tnb[i]);
            for (j=1; j<=3; j++) { tra[nt][j]=tra[i][j]; trb[nt][j]=trb[i][j]; }
            for (j=1; j<=9; j++) { ura[nt][j]=ura[i][j]; urb[nt][j]=urb[i][j]; }
            if (nProc==1) 
              { fprintf(fflog,"\n  template %4d %s %4.2f %3d %s %4.2f %3d",nt,
                        tna[nt],tmsa[nt],cova[nt],tnb[nt],tmsb[nt],covb[nt]); 
                if(us[2]==2){ printf("%4d %s %4.2f %3d %s %4.2f %3d",i,
                        tna[nt],tmsa[nt],cova[nt],tnb[nt],tmsb[nt],covb[nt]); 
                              printf("\n  template "); }}
           }
         *nnt=nt; ier2=0; if (nt==0) ier2=1;
         if (nProc==1) fprintf(fflog,"\n*** No templates");
        }
}
