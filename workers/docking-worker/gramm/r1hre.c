/*
===============================================================================
                                                                        R1HRE.C
                                         Helices restrictions for global search
===============================================================================
*/
#include <math.h>
#include <string.h>

extern float h1uvw[],x[],y[],z[];
extern int   maxa;
extern char  antip[],atmnam[][2][4];

int r1hre(int npb)
{
float h2uvw[5];
float anco,anaco,s1,s2;
int   ang,cb1,cb2;

      cb1=1;                                   /* Terminal CA atoms of mol.B */
      while(1)
        {
         if (strncmp(atmnam[cb1][1]," CA ",4)!=0)
           {
            cb1++; if (cb1>=npb) { cb1=1; break; }    /* in case no CA found */
           }
         else break;
        }
      cb2=npb;
      while(1)
        {
         if (strncmp(atmnam[cb2][1]," CA ",4)!=0)
           {
            cb2--; if (cb2<=1) { cb2=npb; break; }    /* in case no CA found */
           }
         else break;
        }
                                             /* Main axis vector for helix 2 */
      if (antip[0]=='p')
        {h2uvw[1]=x[cb1]-x[cb2];h2uvw[2]=y[cb1]-y[cb2];h2uvw[3]=z[cb1]-z[cb2];}
      else
        {h2uvw[1]=x[cb2]-x[cb1];h2uvw[2]=y[cb2]-y[cb1];h2uvw[3]=z[cb2]-z[cb1];}

      anco=h1uvw[1]*h2uvw[1]+h1uvw[2]*h2uvw[2]+h1uvw[3]*h2uvw[3];

      s1  =h1uvw[1]*h1uvw[1]+h1uvw[2]*h1uvw[2]+h1uvw[3]*h1uvw[3];
      s2  =h2uvw[1]*h2uvw[1]+h2uvw[2]*h2uvw[2]+h2uvw[3]*h2uvw[3];

      s1=(float)sqrt((double)s1); s2=(float)sqrt((double)s2);

      anco=anco/(s1*s2);                      /* Cosine between hel1.& hel.2 */

      anaco=(float)acos((double)anco);
      ang=(int)(anaco*57.3);                   /* Angle between hel1.& hel.2 */

      if (ang<=maxa) return(0);                                   /* allowed */
      else           return(1);                               /* not allowed */
}
