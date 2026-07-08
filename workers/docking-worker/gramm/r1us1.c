/*
===============================================================================
                                                                        R1US1.C
                                                                  User's module
                                                                    Grid output
===============================================================================
flg   0 - mol.A output
      1 - mol.B output
      2 - corr. output
-------------------------------------------------------------------------------
*/
#include <stdio.h>

void r1us2(long,long,long,float *,float,int,int,int);

extern int   npx;
extern FILE  *fres;
 
void r1us1 (int *us,float *ro,float eta3,long ic,int npr,int flg)
{
long  i,j,k,i1,j1,k1;
int   u[10];
int   u0,in,ind;
 
      ind=ic-npr+1;
      switch (flg)
        {
         default :        break;
         case  0 : u0=3;  break;
         case  1:  u0=12; break;
         case  2:  u0=21; break;
        }
      for (in=0; in<=7; in++) u[in]=us[u0+in];

      if ((flg==0)||(flg==1))                                           { 
      if (u[0]==1) {
         for (i=(long)u[1]; i<=(long)u[2]; i+=1l) {
            if ((flg!=2)||(u[7]!=1)) fprintf(fres,"\n");
            for (k=(long)u[5]; k<=(long)u[6]; k+=1l) {
               if ((flg!=2)||(u[7]!=1)) fprintf(fres,"\n");
               for (j=(long)u[3]; j<=(long)u[4]; j+=1l)
                 {if((flg==2)&&(u[7]==1))
                  fprintf(fres,"\n%4ld %4ld ",j,k);
                  r1us2(i,j,k,ro,eta3,ind,u[7],flg); } } } }
      else {
      if (u[0]==2) {
         for (j=(long)u[3]; j<=(long)u[4]; j+=1l) {
            if ((flg!=2)||(u[7]!=1)) fprintf(fres,"\n");
            for (k=(long)u[5]; k<=(long)u[6]; k+=1l) {
               if ((flg!=2)||(u[7]!=1)) fprintf(fres,"\n");
               for (i=(long)u[1]; i<=(long)u[2]; i+=1l)
                 {if((flg==2)&&(u[7]==1))
                  fprintf(fres,"\n%ld %ld ",i,k);
                  r1us2(i,j,k,ro,eta3,ind,u[7],flg); } } } }
      else {
      if (u[0]==3) {
         for (k=(long)u[5]; k<=(long)u[6]; k+=1l) {
            if ((flg!=2)||(u[7]!=1)) fprintf(fres,"\n");
            for (j=(long)u[3]; j<=(long)u[4]; j+=1l) {
               if ((flg!=2)||(u[7]!=1)) fprintf(fres,"\n");
               for (i=(long)u[1]; i<=(long)u[2]; i+=1l)
                 {if((flg==2)&&(u[7]==1))
                  fprintf(fres,"\n%ld %ld ",i,j);
                  r1us2(i,j,k,ro,eta3,ind,u[7],flg); } } } } } }       }

      else                                                             {

      if (u[0]==1) {

         for (i=(long)u[1]; i<=(long)u[2]; i+=1l) 
            {
            if (u[7]!=1) fprintf(fres,"\n");
            i1=i+npx/2; if (i1>npx) i1-=npx;
            for (k=(long)u[5]; k<=(long)u[6]; k+=1l)
               {
               if (u[7]!=1) fprintf(fres,"\n");
               k1=k+npx/2; if (k1>npx) k1-=npx;
               for (j=(long)u[3]; j<=(long)u[4]; j+=1l)
                 {
                  j1=j+npx/2; if (j1>npx) j1-=npx;
                  if(u[7]==1) fprintf(fres,"\n%4ld %4ld ",j1,k1);
                  r1us2(i1,j1,k1,ro,eta3,ind,u[7],flg); } } } }
      else {
      if (u[0]==2) {
         for (j=(long)u[3]; j<=(long)u[4]; j+=1l) 
            {
            if (u[7]!=1) fprintf(fres,"\n");
            j1=j+npx/2; if (j1>npx) j1-=npx;
            for (k=(long)u[5]; k<=(long)u[6]; k+=1l) 
               {
               if (u[7]!=1) fprintf(fres,"\n");
               k1=k+npx/2; if (k1>npx) k1-=npx;
               for (i=(long)u[1]; i<=(long)u[2]; i+=1l)
                 {
                  i1=i+npx/2; if (i1>npx) i1-=npx;
                  if(u[7]==1) fprintf(fres,"\n%ld %ld ",i1,k1);
                  r1us2(i1,j1,k1,ro,eta3,ind,u[7],flg); } } } }
      else {
      if (u[0]==3) {
         for (k=(long)u[5]; k<=(long)u[6]; k+=1l) 
            {
            if (u[7]!=1) fprintf(fres,"\n");
            k1=k+npx/2; if (k1>npx) k1-=npx;
            for (j=(long)u[3]; j<=(long)u[4]; j+=1l)
               {
               if (u[7]!=1) fprintf(fres,"\n");
               j1=j+npx/2; if (j1>npx) j1-=npx;
               for (i=(long)u[1]; i<=(long)u[2]; i+=1l)
                 {
                  i1=i+npx/2; if (i1>npx) i1-=npx;
                  if(u[7]==1) fprintf(fres,"\n%ld %ld ",i1,j1);
                  r1us2(i1,j1,k1,ro,eta3,ind,u[7],flg); } } } } } }      
                                                                       }
}
