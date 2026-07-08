/*
===============================================================================
                                                                        R1US2.C
                                                                  User's module
                                                                    Grid output
===============================================================================
*/
#include <stdio.h>
#include "r1gen.h"
 
extern float g[];
extern float ng3;
extern long  NG2,NG2_2;
extern int   pk[];
extern FILE  *fres;
 
void r1us2 (long i,long j,long k,float *ro,float eta3,int ind,int u,int flg)
{
float gf,roo;
long  gg;
char  c;
 
      if ((flg==0)||(flg==1))
        {
         gf=g[R(i,j,k)];
 
         if((gf>(ro[0]-0.01))&&(gf<(ro[0]+0.01))) c='.'; else {
         if((gf>(ro[1]-0.01))&&(gf<(ro[1]+0.01))) c='*'; else {
         if((gf>(ro[2]-0.01))&&(gf<(ro[2]+0.01))) c='#'; else {
         if((gf>(ro[3]-0.01))&&(gf<(ro[3]+0.01))) c='='; else {
         if((gf>(ro[4]-0.01))&&(gf<(ro[4]+0.01))) c='+'; else {
         if((gf>(ro[5]-0.01))&&(gf<(ro[5]+0.01))) c='o'; else {
                                                  c='?'; }}}}}}
 
         fprintf(fres,"%c",c);     
         if(flg==0) gf*=eta3;
      /* fprintf(fres,"%4.0f",gf); */
        }
      else
        {              roo=ro[0]*ro[0];
         if (u==0)
           {
            gg=(long)(g[R(i,j,k)]*8./((float)pk[ind]*ng3)+1.1);
            if (((g[R(i,j,k)]/ng3)<(roo+0.1))&&
                ((g[R(i,j,k)]/ng3)>(roo-0.1))) gg=(long)roo;
            if (gg==((long)roo)) fprintf(fres," .");
            else
              {
               if (gg<((long)roo)) fprintf(fres," #");
               else       fprintf(fres,"%2ld",gg);
              }
           }
         else
           {
            gf=g[R(i,j,k)]/ng3;
/*          if       ((gf> (roo-0.5))&&(gf<(roo+0.5))) gf=roo;
            else { if (gf<=(roo-0.5))                  gf=roo-1.;}  
            fprintf(fres,"%f",gf);                                  */

            fprintf(fres,"%6.0f",gf);
           }
        }
}
