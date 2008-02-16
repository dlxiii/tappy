#!/usr/bin/env python
"""The pad.py module contains a group of functions to pad values onto the edges
of an n-dimensional array.


"""
# Make sure this line is here such that epydoc 3 can parse the docstrings for
# auto-generated documentation.
__docformat__ = "restructuredtext en"

#===imports======================
import numpy as np

#===globals======================
modname = "pad"
__version__ = "0.2"
__revision__ = "0"

#---other---
__all__ = [
           'minimum',
           'maximum',
           'mean',
           'median',
           'linear_ramp',
           'reflect',
           'constant',
           'wrap',
           ]


########
# Exception classes


class PadWidthWrongNumberOfValues(Exception):
    '''
    Error class for the wrong number of parameters to define the pad width.
    '''
    def __init__(self, rk, pw):
        self.rk = rk
        self.pw = pw

    def __str__(self):
        return "\n\nFor pad_width should get a list/tuple with length \nequal to rank (%i) of lists/tuples with length of 2.  \nInstead have %s" % (self.rk, self.pw)


class NegativePadWidth(Exception):
    '''
    Error class for the negative pad width.
    '''
    def __init__(self):
        pass

    def __str__(self):
        return "\n\nCannot have negative values for the pad_width."


########


########
# Private utility functions.


def __create_vector(vector, pad_tuple, before_val, after_val):
    '''
    Private function which creates the padded vector to mean, maximum,
    minimum, and median.
    '''
    vector[:pad_tuple[0]] = before_val
    if pad_tuple[1] > 0:
        vector[-pad_tuple[1]:] = after_val
    return vector


def __validate_tuple(vector, pad_width):
    '''
    Private function which does some checks and reformats the pad_width
    tuple.
    '''
    pw = None
    shapelen = len(np.shape(vector))
    if (isinstance(pad_width, (tuple, list))
            and isinstance(pad_width[0], (tuple, list))
            and len(pad_width) == shapelen):
        pw = pad_width
    if (isinstance(pad_width, (tuple, list))
            and isinstance(pad_width[0], (int, float, long))
            and len(pad_width) == 1):
        pw = ((pad_width[0], pad_width[0]), ) * shapelen
    if (isinstance(pad_width, (tuple, list))
            and isinstance(pad_width[0], (int, float, long))
            and len(pad_width) == 2):
        pw = (pad_width, ) * shapelen
    if pw == None:
        raise PadWidthWrongNumberOfValues(shapelen, pad_width)
    for i in pw:
        if len(i) != 2:
            raise PadWidthWrongNumberOfValues(shapelen, pw)
        if i[0] < 0 or i[1] < 0:
            raise NegativePadWidth()
    return pw


def __loop_across(matrix, pad_width, function, **kw):
    '''
    Private function to prepare the data for the np.apply_along_axis command
    to move through the matrix.
    '''
    nmatrix = np.array(matrix)
    if 'stat_len' in kw and kw['stat_len']:
        kw['stat_len'] = __validate_tuple(nmatrix, kw['stat_len'])
    else:
        kw['stat_len'] = None
    pad_width = __validate_tuple(nmatrix, pad_width)
    rank = range(len(nmatrix.shape))
    total_dim_increase = [np.sum(pad_width[i]) for i in rank]
    offset_slices = [slice(pad_width[i][0],
                           pad_width[i][0] + nmatrix.shape[i])
                     for i in rank]
    new_shape = np.array(nmatrix.shape) + total_dim_increase
    newmat = np.zeros(new_shape).astype(nmatrix.dtype)
    newmat[offset_slices] = nmatrix

    for iaxis in rank:
        bvec = np.zeros(pad_width[iaxis][0])
        avec = np.zeros(pad_width[iaxis][1])
        np.apply_along_axis(function,
                            iaxis,
                            newmat,
                            pad_width[iaxis],
                            iaxis,
                            bvec,
                            avec,
                            kw)
    return newmat


def __create_stat_vectors(vector, pad_tuple, iaxis, kw):
    '''
    Returns the portion of the vector required for any statistic.
    '''
    pt1 = -pad_tuple[1]
    if pt1 == 0:
        pt1 = None
    sbvec = vector[pad_tuple[0]:pt1]
    savec = vector[pad_tuple[0]:pt1]
    if kw['stat_len']:
        stat_len = kw['stat_len'][iaxis]
        sbvec = np.arange(1)
        savec = np.arange(1)
        if pad_tuple[0] > 0:
            sbvec = vector[pad_tuple[0]:pad_tuple[0] + stat_len[0]]
        if pad_tuple[1] > 0:
            savec = vector[-pad_tuple[1] - stat_len[1]:-pad_tuple[1]]
    return (sbvec, savec)


def __maximum(vector, pad_tuple, iaxis, bvec, avec, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    sbvec, savec = __create_stat_vectors(vector, pad_tuple, iaxis, kw)

    bvec[:] = max(sbvec)
    avec[:] = max(savec)
    return __create_vector(vector, pad_tuple, bvec, avec)


def __minimum(vector, pad_tuple, iaxis, bvec, avec, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    sbvec, savec = __create_stat_vectors(vector, pad_tuple, iaxis, kw)

    bvec[:] = min(sbvec)
    avec[:] = min(savec)
    return __create_vector(vector, pad_tuple, bvec, avec)


def __median(vector, pad_tuple, iaxis, bvec, avec, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    sbvec, savec = __create_stat_vectors(vector, pad_tuple, iaxis, kw)

    bvec[:] = np.median(sbvec)
    avec[:] = np.median(savec)
    return __create_vector(vector, pad_tuple, bvec, avec)


def __mean(vector, pad_tuple, iaxis, bvec, avec, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    sbvec, savec = __create_stat_vectors(vector, pad_tuple, iaxis, kw)

    bvec[:] = np.average(sbvec)
    avec[:] = np.average(savec)
    return __create_vector(vector, pad_tuple, bvec, avec)


def __constant(vector, pad_tuple, iaxis, bvec, avec, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    nconstant = kw['constant_values'][iaxis]
    bvec[:] = nconstant[0]
    avec[:] = nconstant[1]
    return __create_vector(vector, pad_tuple, bvec, avec)


def __linear_ramp(vector, pad_tuple, iaxis, bvec, avec, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    end_value = kw['end_value'][iaxis]
    before_delta = ((vector[pad_tuple[0]] - end_value[0])
                    /float(pad_tuple[0]))
    after_delta = ((vector[-pad_tuple[1] - 1] - end_value[1])
                   /float(pad_tuple[1]))

    before_vector = np.ones((pad_tuple[0], )) * end_value[0]
    before_vector = before_vector.astype(vector.dtype)
    for i in range(len(before_vector)):
        before_vector[i] = before_vector[i] + i*before_delta

    after_vector = np.ones((pad_tuple[1], )) * end_value[1]
    after_vector = after_vector.astype(vector.dtype)
    for i in range(len(after_vector)):
        after_vector[i] = after_vector[i] + i*after_delta
    after_vector = after_vector[::-1]

    return __create_vector(vector, pad_tuple, before_vector, after_vector)


def __reflect(vector, pad_tuple, iaxis, bvec, avec, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    before_vector = (vector[pad_tuple[0] + 1:2*pad_tuple[0] + 1])[::-1]
    after_vector = (vector[-2*pad_tuple[1] - 1:-pad_tuple[1] - 1])[::-1]
    return __create_vector(vector, pad_tuple, before_vector, after_vector)


def __wrap(vector, pad_tuple, iaxis, bvec, avec, kw):
    '''
    Private function to calculate the before/after vectors.
    '''
    before_vector = vector[-(pad_tuple[1] + pad_tuple[0]):-pad_tuple[1]]
    after_vector = vector[pad_tuple[0]:pad_tuple[0] + pad_tuple[1]]
    return __create_vector(vector, pad_tuple, before_vector, after_vector)


########
# Public functions


def maximum(matrix, pad_width=(1, ), stat_len=None):
    """Pads with the maximum value of all or part of the vector along each
    axis.

    Parameters
    ----------
    matrix : array_like
    pad_width : tuple
        how many values padded to each end of the vector for each axis
           ((before, after),) * np.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
    stat_len : tuple
        how many values at each end of vector to calculate the statistic
          ((before_len, after_len),) * np.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions

    Returns
    -------
    array

    See Also
    --------
    pad.minimum
    pad.median
    pad.mean
    pad.constant
    pad.linear_ramp
    pad.reflect
    pad.wrap

    Examples
    --------
    >>> import pad
    >>> a = [1, 2, 3, 4, 5]
    >>> pad.maximum(a, (2,))
    array([5, 5, 1, 2, 3, 4, 5, 5, 5])

    >>> pad.maximum(a, (1, 7))
    array([5, 1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5])

    >>> pad.maximum(a, (0, 7))
    array([1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5])

    """
    return __loop_across(matrix, pad_width, __maximum, stat_len=stat_len)


def minimum(matrix, pad_width=(1, ), stat_len=None):
    """Pads with the minimum value of all or part of the vector along each
    axis.

    Parameters
    ----------
    matrix : array_like
    pad_width : tuple
        how many values padded to each end of the vector for each axis
           ((before, after),) * np.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
    stat_len : tuple
        how many values at each end of vector to calculate the statistic
          ((before_len, after_len),) * np.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions

    Returns
    -------
    array

    See Also
    --------
    pad.maximum
    pad.median
    pad.mean
    pad.constant
    pad.linear_ramp
    pad.reflect
    pad.wrap

    Examples
    --------
    >>> import pad
    >>> a = [1, 2, 3, 4, 5, 6]
    >>> pad.minimum(a, (2,))
    array([1, 1, 1, 2, 3, 4, 5, 6, 1, 1])

    >>> pad.minimum(a, (4, 2))
    array([1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 1, 1])

    >>> a = [[1,2], [3,4]]
    >>> pad.minimum(a, ((3, 2), (2, 3)))
    array([[1, 1, 1, 2, 1, 1, 1],
           [1, 1, 1, 2, 1, 1, 1],
           [1, 1, 1, 2, 1, 1, 1],
           [1, 1, 1, 2, 1, 1, 1],
           [3, 3, 3, 4, 3, 3, 3],
           [1, 1, 1, 2, 1, 1, 1],
           [1, 1, 1, 2, 1, 1, 1]])

    """
    return __loop_across(matrix, pad_width, __minimum, stat_len=stat_len)


def median(matrix, pad_width=(1, ), stat_len=None):
    """Pads with the median value of all or part of the vector along each axis.

    Parameters
    ----------
    matrix : array_like
    pad_width : tuple
        how many values padded to each end of the vector for each axis
           ((before, after),) * np.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
    stat_len : tuple
        how many values at each end of vector to calculate the statistic
          ((before_len, after_len),) * np.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions

    Returns
    -------
    array

    See Also
    --------
    pad.maximum
    pad.minimum
    pad.mean
    pad.constant
    pad.linear_ramp
    pad.reflect
    pad.wrap

    Examples
    --------
    >>> import pad
    >>> a = [1, 2, 3, 4, 5]
    >>> pad.median(a, (2,))
    array([3, 3, 1, 2, 3, 4, 5, 3, 3])

    >>> pad.median(a, (4, 0))
    array([3, 3, 3, 3, 1, 2, 3, 4, 5])

    """
    return __loop_across(matrix, pad_width, __median, stat_len=stat_len)


def mean(matrix, pad_width=(1, ), stat_len=None):
    """Pads with the mean value of all or part of the vector along each axis.

    Parameters
    ----------
    matrix : array_like
    pad_width : tuple
        how many values padded to each end of the vector for each axis
           ((before, after),) * np.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
    stat_len : tuple
        how many values at each end of vector to calculate the statistic
          ((before_len, after_len),) * np.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions

    Returns
    -------
    array

    See Also
    --------
    pad.maximum
    pad.minimum
    pad.median
    pad.constant
    pad.linear_ramp
    pad.reflect
    pad.wrap

    Examples
    --------
    >>> import pad
    >>> a = [1, 2, 3, 4, 5]
    >>> pad.mean(a, (2,))
    array([3, 3, 1, 2, 3, 4, 5, 3, 3])

    """
    return __loop_across(matrix, pad_width, __mean, stat_len=stat_len)


def constant(matrix, pad_width=(1, ), constant_values=(0, )):
    """Pads with a constant value.

    Parameters
    ----------
    matrix : array_like
    pad_width : tuple
        how many values padded to each end of the vector for each axis
           ((before, after),) * np.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
    constant: tuple
        the value to set the padded values to
          ((before_constant, after_constant),) * np.rank(matrix)
          (constant,) is a shortcut for before = after = constant for all
          dimensions

    Returns
    -------
    array

    See Also
    --------
    pad.maximum
    pad.minimum
    pad.median
    pad.mean
    pad.linear_ramp
    pad.reflect
    pad.wrap

    Examples
    --------
    >>> import pad
    >>> a = [1, 2, 3, 4, 5]
    >>> pad.constant(a, (2,3), (4,6))
    array([4, 4, 1, 2, 3, 4, 5, 6, 6, 6])

    """
    constant_values = __validate_tuple(matrix, constant_values)
    return __loop_across(matrix,
                         pad_width,
                         __constant,
                         constant_values=constant_values)


def linear_ramp(matrix, pad_width=(1, ), end_value=(0, )):
    """Pads with the linear ramp between end_value and the begining/end of the
    vector along each axis.

    Parameters
    ----------
    matrix : array_like
    pad_width : tuple
        how many values padded to each end of the vector for each axis
           ((before, after),) * np.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes
    end_value: tuple
        value to ramp to
          ((before_len, after_len),) * np.rank(matrix)
          (len,) is a shortcut for before = after = len for all dimensions

    Returns
    -------
    array

    See Also
    --------
    pad.maximum
    pad.minimum
    pad.median
    pad.mean
    pad.constant
    pad.reflect
    pad.wrap

    Examples
    --------
    >>> import pad
    >>> a = [1, 2, 3, 4, 5]
    >>> pad.linear_ramp(a, (2,3), (5,-4))
    array([ 5,  3,  1,  2,  3,  4,  5,  2, -1, -4])

    """
    end_value = __validate_tuple(matrix, end_value)
    return __loop_across(matrix, pad_width, __linear_ramp, end_value=end_value)


def reflect(matrix, pad_width=(1, )):
    """Pads with the reflection of the vector mirrored on the first and last
    values of the vector along each axis.

    Parameters
    ----------
    matrix : array_like
    pad_width : tuple
        how many values padded to each end of the vector for each axis
           ((before, after),) * np.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes

    Returns
    -------
    array

    See Also
    --------
    pad.maximum
    pad.minimum
    pad.median
    pad.mean
    pad.constant
    pad.linear_ramp
    pad.wrap

    Examples
    --------
    >>> import pad
    >>> a = [1, 2, 3, 4, 5]
    >>> pad.reflect(a, (2,3))
    array([3, 2, 1, 2, 3, 4, 5, 4, 3, 2])

    """
    # TODO self.pad_length_before & self.pad_length_after < len(self.vector)
    return __loop_across(matrix, pad_width, __reflect)


def wrap(matrix, pad_width=(1, )):
    """Pads with the wrap of the vector along the axis.  The first values are
    used to pad the end and the end values are used to pad the beginning.

    Parameters
    ----------
    matrix : array_like
    pad_width : tuple
        how many values padded to each end of the vector for each axis
           ((before, after),) * np.rank(matrix)
           (pad,) is a shortcut for before = after = pad for all axes

    Returns
    -------
    array

    See Also
    --------
    pad.maximum
    pad.minimum
    pad.median
    pad.mean
    pad.constant
    pad.linear_ramp
    pad.reflect
    pad.wrap

    Examples
    --------
    >>> import pad
    >>> a = [1, 2, 3, 4, 5]
    >>> pad.wrap(a, (2,3))
    array([4, 5, 1, 2, 3, 4, 5, 1, 2, 3])

    """
    return __loop_across(matrix, pad_width, __wrap)


########


if __name__ == '__main__':
    ''' This section is just used for testing.  Really you should only import
        this module.
    '''
    arr = np.arange(100)
    print arr
    print median(arr, (3, ))
    print constant(arr, (-25, 20), (10, 20))
    arr = np.arange(30)
    arr = np.reshape(arr, (6, 5))
    print mean(arr, pad_width=((2, 3), (3, 2), (4,5)), stat_len=(3, ))
