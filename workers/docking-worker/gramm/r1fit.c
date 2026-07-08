/*
===============================================================================
                                                                        R1FIT.C
                                              Molecule B processing and fitting
===============================================================================
*/
#include <stdio.h>
#include <mpi.h>

void r1rot(long,float,int);
void r1dig(float,int,int,float,int,int);
void r1fft(int);
void r1ffw(int);
void r1mul(void);
void r1pek(int,long,long,long *,int *);
int  r1hre(int);
void r1us1(int *,float *,float,long,int,int);
void r1us3(int *,float,int);
 
extern float g[];
extern long  sh[],ino[];
extern long  NG2_3;
extern int   pk[];
extern int   nurtog,ctiv,ier2;
extern char  mmode[];
extern FILE  *fflog;

extern int myProc, nProc;
extern MPI_Status *mpi_status;
 
void r1fit (int npb,int hcb,float *ro,float eta3,long *nor,float cmb,int npr,
            float rpi,int *us)
{
float rad,pmax;
long  i,rii,norr,ir,ic;
long  beg,end,block,ibeg,iblock;
int   m,fl,cumm;
int   ipc;
 
      m=1;                                                     /* Mol.B flag */
      ic=0l;                                                /* Peaks counter */
      rii=(long)(rpi*rpi);                        /* Radius of peak identity */
      norr=(*nor);               /* Reduced no.of rotations (for spec.cases) */
      nurtog=0;                /* Toggle for binding site residues (overlap) */

      if(us[0]) r1us3(us,cmb,npb);                       /* Initial rotation */
 		
/* -----------------------Start Parallel GRAMM------------------------ */
/* Block decomposition of rotations */
      block=(*nor/(long)nProc);
      beg  = (long)myProc * block + 1l;
      end  =((long)myProc + 1l) * block;  if(myProc == nProc - 1) end = *nor;
       
      for (ir=beg; ir<=end; ir+=1l) /* Parallel */
        {
         r1rot(ir,cmb,npb);                                      /* Rotation */

         if((mmode[0]=='h')&&(r1hre(npb))){norr-=1l; continue;}/*Helix restr */
 
         if ((mmode[0]=='d')||(mmode[0]=='h'))       /* Docking digitization */ 
           {
            rad=0.; fl=1;
            r1dig(rad,npb,hcb,ro[1],m,fl);
           }
         else                                        /* Overlap digitization */
           {
            rad=1.; fl=1; nurtog=0;               /* inflated image with 1's */
            r1dig(rad,npb,hcb,1,m,fl);
           
            if (ctiv) cumm=1; else cumm=0;            
            ctiv=0;

            rad=0.; fl=1; nurtog=0;                         /* core with 0's */
            r1dig(rad,npb,hcb,0,m,fl);

            rad=1.; fl=1; nurtog=1;           /* blackout nonbinding surface */
            r1dig(rad,npb,hcb,0,m,fl); 

            if (cumm) ctiv=1; 
           }
/*---------------------------------------------------- Projection processing */
/*         pmax=0.;                                                          */
/*         for (i=1l; i< NG2_3; i+=2l) { if (pmax<g[i]) pmax=g[i]; }         */
/*         for (i=1l; i< NG2_3; i+=2l)                                       */
/*           { */
/*            if (g[i]==0.) continue;                */        /* background */
/*            g[i+1]=g[i]; g[i]=pmax-g[i];           */        /*    surface */
/*           }                                                               */
/*---------------------------------------------------------------------------*/
         if (us[0]&&us[12]) r1us1(us,ro,eta3,0,0,1);
 
         if (us[0]&&us[51]) r1fft(1); else r1ffw(1);                  /* FFT */
 
         r1mul();                                          /* Multiplication */
 
         if (us[0]&&us[51]) r1fft(-1); else r1ffw(-1);              /* I-FFT */
 
         r1pek(npr,rii,ir,&ic,us);                            /* Peak search */
         if (us[0]&&us[21]) r1us1(us,ro,eta3,ic,npr,2);

         for (i=1l; i<=NG2_3; i+=1l) g[i]=0.;          /* Clean for next iter*/
        }
/* send number of peaks to share */
/* send peaks array */
      if(myProc != 0)
        {
         MPI_Send(&ic,     1, MPI_LONG, 0, 1, MPI_COMM_WORLD);	
         MPI_Send(&pk[1], ic, MPI_INT,  0, 1, MPI_COMM_WORLD);
         MPI_Send(&sh[1], ic, MPI_LONG, 0, 1, MPI_COMM_WORLD);
         MPI_Send(&ino[1],ic, MPI_LONG, 0, 1, MPI_COMM_WORLD);
		}
   /* root proc 0 receives send count to iblock & receives peaks into own pk */	
      else if(nProc > 1)     /* process 0 only in parallel execution context */
		{
		 ibeg = ic + 1l;/* start after process 0 peaks since root is a worker*/
		 for(ipc=1; ipc < nProc; ipc++)
		   {
            MPI_Recv(&iblock,        1,MPI_LONG,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&pk[ibeg], iblock,MPI_INT, ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&sh[ibeg], iblock,MPI_LONG,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
            MPI_Recv(&ino[ibeg],iblock,MPI_LONG,ipc,1,MPI_COMM_WORLD,MPI_STATUS_IGNORE);
			ibeg = ibeg + iblock; 
		   }
		}	
/*--------------------------- End Parallel Gramm -------------------------*/

      if (norr<=0l) 
        { 
         fprintf(fflog,"\n*** ERROR: no complex matches the restrictions\n\n");
         ier2=1; return; 
        }
      *nor=norr;
}
