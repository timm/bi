
(defmacro dovs ((one two v1 v2 &optional out) &body body)
  (let ((i  (gensym)) (l3 (gensym)) 
	(v3 (gensym)) (v4 (gensym)))
    `(let* ((,v3 ,v1)
	        (,v4 ,v2)
		    (,l3 (length ,v3)))
       (do-nums (,i ,l3 ,out)
		 (let ((,one (svref ,v3 ,i)) 
		              (,two (svref ,v4 ,i)))
		      ,@body)))))

(defmacro dov ((one  v &optional out) &body body)
  (let ((i (gensym)))
    `(dotimes (,i (length ,v) ,out)
       (let ((,one (svref ,v ,i)))
	  ,@body))))
  
(defun anyv (v)
  (svref v (random (length v))))

(defun dist (this that)
  "Ignores the class variable -- effort in our case."
  (let ((d 0))
    (dotimes (n (1- (length this)))
      (if (numberp (svref this n))
(setf d (+ d (expt (- (svref that n) (svref this n)) 2)))
(if (eql (svref this n) (svref that n))
(incf d))))
    (sqrt d)))

(defun find-poles (rows)
  (let* ((any (anyv rows))
	 (east (furthest-away any rows))
	 (west (furthest-away east rows)))
    (values west east)))

(defun furthest-away (row rows)
  (let ((max -1) 
	out)
    (dov (tmp rows (values out max))
	 (let ((d (dist row tmp)))
	   (when (> d max)
	     (setf max d
		   out tmp))))))


(defun xy (here west east)
  (let* ((a2 (expt (dist west here) 2))
	(b2 (expt (dist east here) 2))
	(base_d (dist west east))
	(x (/ (- b2 (expt base_d 2) a2)
	      (* -2
		 base_d)))
	(y (sqrt (- a2 (expt x 2)))))
    (values x y)))