/*
===============================================================================
                                                                        R1RHA.C
                                                     Assign parameters to atoms
===============================================================================
*/
#include <string.h>

void r1srt(int);

extern float ra[][2],hy[][2],ws[];
extern long  ind[];
extern int   inn[][2];
extern char  typat[][2][4];
 
void r1rha (typ,hh,rr,npar,np,m,rm)
 
float hh[],rr[];
float *rm;
int   npar,np,m;
char  typ[][4];
{
int   i,ip,si;
 
      *rm=0.;
      for (i=1; i<=np; i++)                                        /* Assign */
        {
         for (ip=1; ip<=npar; ip++)
           {
            if ((si=strncmp(typat[i][m],typ[ip],4))) continue;
            ra[i][m]=rr[ip]; hy[i][m]=hh[ip]; break;
           }
         if (*rm<ra[i][m]) *rm=ra[i][m];                          /* Max. rm */
        }
      for (i=1; i<=np; i++) { ws[i]=hy[i][m]; ind[i]=i; }
      r1srt(np);                                  /* Sort (hydrophobic last) */
      for (i=1; i<=np; i++) inn[i][m]=ind[i];
}
