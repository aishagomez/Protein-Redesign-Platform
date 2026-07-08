/*
===============================================================================
                                                                        R1MUL.C
                                                 Multiplication of the matrices
===============================================================================
*/
extern float g[],g1[];
extern long  NG2_3;
 
void r1mul()
{
float r1,r2,i1,i2;
long  i,ii;
 
      for (i=1l; i< NG2_3; i+=2l)
        {
         ii=i+1l;
         r1=g1[i]; i1=g1[ii];
         r2=g[i];  i2=g[ii];
         g[i]=r1*r2-i1*i2; g[ii]=r1*i2+r2*i1;
        }
}
