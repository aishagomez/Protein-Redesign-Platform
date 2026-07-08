/*
===============================================================================
                                                                        W1SCO.C
                                                                Scoring low-res
===============================================================================
*/
#include <string.h>

void w1vdw(int,int,int,float *);
void w1sta(int,int,int,float *);
void cnpst(int *,int *,int,int,int,int,float *);

extern int   energy[];

void w1sco(int scovdw,int scosta,int ctr,int npa,int npb,int *conresa,
           int *conresb,int conwei_p,int conwei_n,int beg,int *ic)
{
float env,ens,enc;

      env=ens=enc=0.;

      if (scovdw) w1vdw(scovdw,npa,npb,&env);                /* VDW off grid */

      if (scosta) w1sta(scosta,npa,npb,&ens);       /* Statistical potential */

      if (ctr) cnpst(conresa,conresb,conwei_p,conwei_n,npa,npb,&enc);/*Constr*/

      *ic=(*ic)+1;
      energy[(*ic)]=(int)env+(int)ens+(int)enc;

//    with scan contribution:
//    energy[(*ic)]=energy[(*ic)+beg-1]+(int)env+(int)ens+(int)enc;
}
