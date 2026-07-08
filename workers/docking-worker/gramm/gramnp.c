/*
===============================================================================
G R A M M  v2.0                                                        GRAMNP.C
Global Range Molecular Matching                                    Main program
===============================================================================
*/
#include <stdio.h>
#include <string.h>
#include <mpi.h>
#include "r1dim.h"
#include "t1dim.h"
#include "w1dim.h"
#include "r1glo.h"
#include "t1glo.h"
#include "w1glo.h"

void r1opr(void);
void t1opr(void);
void w1opr(void);

int main(int argc,char *argv[])
{
int   tri,sca,tb,ref;

/*------------------------------------------ Initialize parallel environment */
      MPI_Init(&argc, &argv);
      MPI_Comm_group(MPI_COMM_WORLD, &MPI_GROUP_WORLD);
      MPI_Comm_rank(MPI_COMM_WORLD, &myProc);
      MPI_Comm_size(MPI_COMM_WORLD, &nProc);

/*----------------------------------------------- Initialize log, parameters */
      fflog=fopen("gramm.log","w"); sca=tb=ref=0;

/*------------------------------------------------- Arguments passed to main */
      if (argc==1) 
        {
         fprintf(fflog,"\n*** ERROR: no parameters (scan,tb,refine)");
         fprintf(fflog," for GRAMM\n\n"); return 0; /* insted of old exit(0) */
        }

      tri=strcmp(argv[1],"scan");                           /* 1st parameter */
      if (tri==0) sca=1;   else     {
      tri=strcmp(argv[1],"tb");
      if (tri==0) tb=1;    else     {
      tri=strcmp(argv[1],"refine");
      if (tri==0) ref=1;   else     {
      fprintf(fflog,"\n*** ERROR: wrong parameter %s\n\n",argv[1]); 
      return 0;                    }}}
      
      if (argc==3)
        {
         tri=strcmp(argv[2],"scan");
         if (tri==0) 
           { fprintf(fflog,"\n*** ERROR: wrong sequence of operations\n\n");
             return 0; }
         tri=strcmp(argv[2],"tb");
         if (tri==0) 
           { fprintf(fflog,"\n*** ERROR: wrong sequence of operations\n\n");
             return 0; }
         tri=strcmp(argv[2],"refine");
         if (tri==0) ref=1;   else     {
         fprintf(fflog,"\n*** ERROR: wrong parameter %s\n\n",argv[2]); 
         return 0;                     }
        }
      
      if (argc>3) 
        { fprintf(fflog,"\n*** ERROR: too many parameters\n\n"); return 0; }
         
/*---------------------------------------------------------------------------*/

      if (sca)                                                /* GLOBAL Scan */
        { r1opr(); if(ier1||ier2)return 0; }

      if (tb)                                              /* GLOBAL TB Scan */
        { t1opr(); if(ier1||ier2)return 0; }

      if (ref)                                           /* LOCAL Refinement */
        { w1opr(); if(ier1||ier2)return 0; }

/*-------------------------------------------------------- End parallel proc */
      MPI_Finalize();
}
