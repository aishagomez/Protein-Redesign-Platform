/*
===============================================================================
                                                                        R1SRT.C
                                                                        Sorting
===============================================================================
*/
extern float ws[];
extern long  ind[];   /* index */
 
void r1srt (int n)
{
float rra;
long  rrb;
int   l,j,ir,i;
 
      l=(n>>1)+1; ir=n;
      for (;;)
        {
         if (l>1) { rra=ws[--l]; rrb=ind[l]; }
         else {     rra=ws[ir];  rrb=ind[ir];
                           ws[ir]=ws[1]; ind[ir]=ind[1];
            if (--ir==1) { ws[1] =rra;   ind[1] =rrb; return; } }
         i=l; j=l<<1;
         while (j<=ir)
           {
            if (j<ir&&ws[j]<ws[j+1]) ++j;
            if (rra<ws[j]) { ws[i]=ws[j]; ind[i]=ind[j]; j+=(i=j); }
            else j=ir+1;
           }
         ws[i]=rra; ind[i]=rrb;
        }
}
