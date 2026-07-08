/*
===============================================================================
                                                                        R1FLT.C
                                                        Highest peaks treatment
===============================================================================
*/
void r1srt(int);
 
extern float ws[];
extern long  in[],ind[];
extern int   pk[];
 
void r1flt (float th,long nor,int npr,int *npek)
{
long  ir,npt;
int   pth,ic;
 
      npt=nor*(long)npr;
 
      if (npt==1l) { *npek=1; in[1]=1l; return; }
 
      pth=0;                                        /* Threshold calculation */
      for (ir=1l; ir<=npt; ir+=1l)
        {
         if (pth<pk[ir]) pth=pk[ir];
        }
      pth=(int)(((float)pth)*th);
                                                                /* Filtering */
      ic=0;
      for (ir=1l; ir<=npt; ir+=1l)
        {
         if (pth>pk[ir]) continue;
         ic++; pk[ic]=pk[ir]; in[ic]=ir;
        }
      *npek=ic;
 
      if (*npek==1) return;
                                                                  /* Sorting */
      for(ir=1;ir<=*npek;ir++)
        { ws[ir]=(float)(-pk[ir]); ind[ir]=in[ir]; }
      r1srt(*npek);                                /* pk[],in[] ascend.order */
 
      for(ir=1;ir<=*npek;ir++)                              /* descend.order */
        { pk[ir]=(int)(-ws[ir]); in[ir]=ind[ir]; }
}
