(define (problem elevator fnp1)
   (:domain miconic)
   (:objects p0 - passenger
             f0 f1 - floor)


(:init
(succ f0 f1)



(origin p0 f0)
(destin p0 f0)
(origin p0 f1)
(destin p0 f1)



(lift-at f0)
)


(:goal
(and
(served p0)
))
)


