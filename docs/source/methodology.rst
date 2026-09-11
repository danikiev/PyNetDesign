.. _methodology:

===========
Methodology
===========

This chapter presents the theory behind PyNetDesign. It describes how the minimum
detectable moment magnitude of a microseismic event is evaluated for a network of
receivers in a homogeneous, isotropic and attenuating medium, separately for each
seismic phase and for each receiver type.

.. note::

   PyNetDesign models a homogeneous medium. The ray path between a source and a
   receiver is therefore a straight line, there are no interfaces and no transmission
   losses, and geometrical spreading is simply proportional to distance.

----

.. _spectral_conventions:

Spectral conventions and source-model assumption
================================================

We work with frequency in Hz, :math:`f`, and angular frequency :math:`\omega = 2\pi f`.

Let :math:`|U(f)|` denote the amplitude spectrum magnitude of **particle displacement** (projected onto the considered phase polarization) recorded at the receiver.
If the instrument measures particle velocity, the corresponding spectrum is

.. math::
   :label: velocity_displacement_relation

   |V(f)| = 2\pi f\,|U(f)|,

which follows from :math:`v(t)=\dot{u}(t)`.

For shear-dominated microseismic events we adopt the standard :math:`\omega^{-2}` source model :cite:p:`AkiRichards2002`. 
The source displacement spectrum is

.. math::

   \Omega_D(f)=
   \begin{cases}
   C_0 M_0, & f < f_c, \\
   C_0 M_0 \left(\dfrac{f_c}{f}\right)^2, & f \ge f_c,
   \end{cases}

where :math:`M_0` is seismic moment, :math:`f_c` is corner frequency, and :math:`C_0` contains radiation-pattern and medium constants.

We define

.. math::

   \Omega_0 \equiv C_0 M_0,

which is the low-frequency (plateau) level of the far-field source displacement spectrum.

We assume a representative frequency :math:`f` below the corner frequency (:math:`f < f_c`, often :math:`f=f_{\mathrm{peak}}`, see Section :ref:`peak_frequency`), so the source spectrum is approximately flat, :math:`\Omega_D(f) \approx \Omega_0`.
In this regime, the source spectral function reduces to its low-frequency limit and can be approximated as unity.

----

.. _intrinsic_attenuation:

Intrinsic attenuation
=====================

The attenuation operator :math:`t^*` (known as global absorption factor :cite:p:`Cerveny2001`) is the path integral along the ray:

.. math::
    :label: tstar

    t^* = \int_R \frac{dr}{v(r)\,Q(r)},

For a homogeneous medium, where :math:`v` and :math:`Q` are constant along the
straight ray of length :math:`r`, Equation :eq:`tstar` reduces to

.. math::
    :label: tstar_homo

    t^* = \frac{r}{vQ}.

----

.. _peak_frequency:

Peak frequency
==============

The peak frequency of an observed signal is the frequency corresponding to the maximum amplitude in Fourier spectra of the particle velocity. 
As shown by :cite:t:`EisnerGeiEtAl2013`, the peak frequency can be determined for geophone recordings (i.e., particle velocity) from the global absorption factor :math:`t^*` only. 
The particle velocity is convenient mainly because most of the observations are carried out on instruments recording particle velocity (e.g., geophones or even broadband seismometers).

In Section :ref:`spectral_conventions` we have shown that the Fourier spectrum of particle displacement is flat at low frequencies with nonzero permanent displacement at the source :cite:p:`AkiRichards2002`. 
At higher frequencies, the source spectrum is limited by the rise and rupture times of an earthquake fault rupture. 
These limitations result in a sharp slope change of spectral power density of the particle displacement spectrum. 
This abrupt change in slope occurs at a corner frequency :math:`f_c`.
Hence, the peak of this positive function must occur for frequencies at or below the corner frequency :cite:p:`EisnerGeiEtAl2013`.

The peak frequency :math:`f_{\mathrm{peak}}` is the frequency of the maximum amplitude in the particle velocity spectra. 
Propagation attenuation modifies the observed spectrum through the global absorption factor :math:`t^*` (e.g., :cite:t:`Cerveny2001`, :cite:t:`EisnerGeiEtAl2013`):

.. math::

   |V(f)| \propto f\, e^{-\pi f t^*}.

Maximization of this expression for :math:`f < f_c` yields

.. math::
   :label: fpeak

   f_{\mathrm{peak}} = \frac{1}{\pi t^*},

where :math:`t^*` is evaluated according to Equation :eq:`tstar`.

.. note::

    Equation :eq:`fpeak` is only valid  for :math:`f < f_c`, i.e., when the source spectrum is approximately flat. 
    If not, the maximum occurs at the boundary :math:`f_{\mathrm{peak}}=f_c`.

Similarly, the peak amplitude for particle acceleration will occur at a frequency twice bigger than those for particle velocity, i.e., at :math:`f_{\mathrm{peak}}=2/(\pi t^*)`.

Taking into account Equation :eq:`tstar_homo`, in homogeneous medium the peak amplitude for particle velocity is

.. math::
    :label: fpeak_homo

    f_{\mathrm{peak}} = \frac{vQ}{\pi r},

where :math:`v` is the body wave velocity (P- or S-wave), :math:`Q` is the attenuation factor (P- or S-wave), and :math:`r` is the distance from a source to a receiver.

----


.. _detection_threshold:

Detection threshold
===================

An event is considered detected on a receiver when the amplitude of the arriving phase
exceeds the local noise level by a required factor. For receiver :math:`i` the minimum
detectable displacement amplitude spectrum is

.. math::
    :label: min_amplitude

    |U_{\min,i}(f)| = D_{\mathrm{SNR}}\,A_{N,i}\,S(f),

where :math:`A_{N,i}` is the measured noise level of that receiver,
:math:`D_{\mathrm{SNR}}` is the signal-to-noise ratio required for detection, and
:math:`S(f)` converts the recorded quantity to a displacement amplitude spectrum.

Following Equation :eq:`velocity_displacement_relation`, the conversion coefficient is

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Recorded quantity
     - :math:`S(f)`
     - Comment
   * - displacement
     - :math:`1`
     - already a displacement
   * - particle velocity
     - :math:`(2\pi f)^{-1}`
     - from :math:`|V(f)| = 2\pi f\,|U(f)|`
   * - particle acceleration
     - :math:`(2\pi f)^{-2}`
     - two integrations
   * - strain
     - :math:`L_g`
     - strain averaged over the gauge length :math:`L_g`
   * - strain rate
     - :math:`L_g / (2\pi f)`
     - as strain, plus one integration in time

For DAS, the recorded quantity is the strain or strain rate along the cable, averaged
over the gauge length :math:`L_g`. Multiplying by :math:`L_g` converts it to an
equivalent displacement, which assumes the strain to be constant over the gauge length.

The threshold is then corrected for the receiver response of
Section :ref:`das_directionality`, giving the polarization-aligned threshold
:math:`\widetilde{U}_{\min,i}^{\phi} = C_\phi\,|U_{\min,i}(f)|` for phase :math:`\phi`,
and divided by the free-surface factor of Section :ref:`free_surface_boundary_condition`
for receivers at the surface.

.. _network_detectability:

Network detectability
=====================

Inserting the threshold into Equation :eq:`seismic_moment_homogeneous` and converting to
a magnitude yields a per-receiver threshold magnitude
:math:`M_w^{\min}(\mathbf{x}, i)` for every grid point :math:`\mathbf{x}` and every
receiver :math:`i`.

An event is only useful if it is seen on several receivers. Sorting the per-receiver
values at a grid point in ascending order, the network threshold for a phase is the
:math:`N`-th smallest value, where :math:`N` is the minimum number of receivers required
for detection. For joint P- and S-wave detection, the stricter of the two phase
thresholds applies,

.. math::

    M_w^{\min} = \max\!\left(M_w^{\min,P},\; M_w^{\min,S}\right).

For the composite ``S`` mode, the SV and SH branches are evaluated separately for each
source-receiver pair and the more detectable branch, that is the smaller magnitude, is
retained. A phase whose projection vanishes is excluded rather than treated as
infinitely detectable.

----

.. _free_surface_boundary_condition:

Free surface boundary condition
===============================

At the free surface boundary, incoming body waves are reflected, resulting in a complex interference pattern that modifies the recorded amplitude. 
For the purposes of detectability, we approximate the recorded displacement amplitude to be twice that of the incident wave. 
This approximation corresponds exactly to the free-surface amplification factor for normal or near-normal incidence, as derived from the free-surface reflection equations (:cite:t:`AkiRichards2002`, Section 5.2.2).

----

.. _das_directionality:

Receiver projection and DAS directionality
==========================================

PyNetDesign treats ordinary geophones as three-component receivers by default.
For these receivers the recorded scalar amplitude is assumed to be aligned with the arriving phase polarization, so no projection loss is applied.
If a station geometry row has :code:`Components=Z`, the arriving displacement is projected onto the vertical axis.
For DAS receivers, PyNetDesign applies the same phase-dependent projection logic onto the local fiber tangent :math:`\boldsymbol\tau`.

In a homogeneous medium the ray is a straight line, so the phase polarization is computed from the straight receiver-to-grid direction.
The amplitude correction for phase :math:`\phi` and receiver direction :math:`\mathbf d` is

.. math::

   C_\phi =
   \frac{1}{|\mathbf d \cdot \mathbf e_\phi|},

where :math:`\mathbf d` is :math:`\hat{\mathbf z}` for vertical-component geophones and :math:`\boldsymbol\tau` for DAS.
:math:`\mathbf e_P` is the longitudinal P polarization, :math:`\mathbf e_{SV}` is the transverse polarization in the local vertical ray plane, and :math:`\mathbf e_{SH}` is perpendicular to that plane.
The corrected minimum recorded amplitude is multiplied by :math:`C_\phi`.
For composite ``S`` mode, SV and SH are corrected separately and the more detectable branch is retained.

If the projection is zero, that phase is not observable on the selected receiver component for that source-station pair.
For example, SH is horizontal in the current isotropic convention and is therefore not recorded by a vertical-component geophone.

For nearly vertical rays, the explicit SV/SH azimuthal basis is convention-dependent because the horizontal ray azimuth is poorly defined.
PyNetDesign uses a stable horizontal fallback basis in this case; the composite ``S`` mode is the practical robust choice when only S-wave detectability is required.

----

.. _radiation_pattern:

Radiation pattern
=================

In the far field, body-wave amplitudes from a seismic moment tensor source depend on the take-off direction and on the wave polarization.
Let :math:`\mathbf n` be the unit vector in the P-wave take-off direction at the source (pointing from source to receiver), and let :math:`\mathbf e` be the unit polarization vector of the considered phase at the source.

Following the quantitative formulation of :cite:t:`AkiRichards2002` (Section 4.5), for a moment tensor :math:`\mathbf M`, the dimensionless scalar radiation pattern factor for the phase with polarization :math:`\mathbf e` is

.. math::

    R(\mathbf n,\mathbf e)
    =
    \frac{\mathbf e^{T}\,\mathbf M\,\mathbf n}{M_0},

where :math:`M_0` is the scalar seismic moment (used only for normalization of the dimensionless factor).

For P waves, the polarization is longitudinal (:math:`\mathbf e=\mathbf n`), leading to the familiar radiation pattern factor (:cite:t:`AkiRichards2002`, Eq. 4.89):

.. math::

    R_P = \frac{\mathbf n^{T}\,\mathbf M\,\mathbf n}{M_0}.

For S waves, there are two orthogonal transverse polarizations. 
Denoting by :math:`\mathbf s_{SV}` the unit SV polarization (in the ray plane) and by :math:`\mathbf s_{SH}` the unit SH polarization (perpendicular to the ray plane), the corresponding radiation factors are (:cite:t:`AkiRichards2002`, Eqs. 4.90 and 4.91):

.. math::

    R_{SV} = \frac{\mathbf s_{SV}^{T}\,\mathbf M\,\mathbf n}{M_0},
    \qquad
    R_{SH} = \frac{\mathbf s_{SH}^{T}\,\mathbf M\,\mathbf n}{M_0}.

In this documentation and in the magnitude-sensitivity formulas, :math:`|R|` denotes the **magnitude** of the appropriate factor (:math:`|R_P|` for P, :math:`|R_{SV}|` for SV, and :math:`|R_{SH}|` for SH).
For ``wave_mode="S"``, PyNetDesign evaluates SV and SH separately and keeps the more detectable branch for each source-station pair.

For microseismic network design, the source mechanism and take-off directions are often unknown. 
In that case, it is common to use an *effective* radiation-pattern magnitude (i.e., a somehow averaged value of :math:`|R|` over a suitable ensemble of mechanisms and directions).
:cite:t:`HalloEisner2013` following :cite:t:`BooreBoatwright1984` suggest to use representative RMS values for DC seismic sources :math:`R_P^{\mathrm{eff}} = \sqrt{\langle R_P^2\rangle} \approx 0.52` and :math:`R_S^{\mathrm{eff}} = \sqrt{\langle R_S^2\rangle} \approx 0.63`.
PyNetDesign uses fixed RMS constants :math:`R_P^{\mathrm{eff}}=\sqrt{4/15}\approx 0.516`, :math:`R_{SV}^{\mathrm{eff}}=\sqrt{7/30}\approx 0.483` for SV and :math:`R_{SH}^{\mathrm{eff}} = \sqrt{1/6}\approx 0.408` for SH.
See Section :ref:`derivation_radiation_pattern` for more information.

----

.. _magnitude_sensitivity:

Magnitude sensitivity
=====================

The magnitude sensitivity module is designed to estimate the magnitudes of microseismic events that can be theoretically detected by the network of receivers. 
This sensitivity (or detectability) varies in space and hence it is presented in the form of horizontal or vertical slices in the 3D space. 
PyNetDesign uses attenuation of the dominant signal (based on the quality factor of the medium :math:`Q` ), and signal-to-noise ratio (SNR) necessary for seismic event detection.
Results depend on a model of attenuation, noise, wave velocity, and detection method. 
The resulting sensitivity can show the spatial distribution of the minimal technically detectable magnitude, or, in other words, the spatial distribution of the magnitude of detection catalogue completeness. 
The moment magnitude of an event, according to :cite:t:`Kanamori1977`, is given by logarithm of the scalar value of the seismic moment:

.. math::
    M_w = \frac{2}{3}\left(\log_{10}(M_0)-9.1\right),

where :math:`M_0` is the seismic moment.

PyNetDesign computes minimal moment magnitude of an event, which will theoretically produce amplitudes on receivers necessary for the event detection. 
Amplitude levels for the event detection are dependent on local noise levels and signal-to-noise ratio necessary for particular detection method.

.. _homogeneous_medium:

Homogeneous medium
------------------

In a homogeneous isotropic medium, the scalar seismic moment :math:`M_0` can be related to the magnitude of the displacement Fourier spectrum :math:`|U(f)|` (projected onto the arriving polarization of the considered phase P or S) at frequency :math:`f` as

.. math::
    :label: seismic_moment_homogeneous

    M_0
    =
    \frac{4 \pi \rho v^3 r}{|R|}
    \;|U(f)|\;
    \exp\!\big(\pi f\,t^*\big),

where :math:`\rho` is density, :math:`v` is the body-wave velocity (:math:`v=\alpha` for P waves, :math:`v=\beta` for S waves), and :math:`r` is the source-receiver distance.
The factor :math:`|R|` is the dimensionless radiation-pattern magnitude for the considered phase, consistent with the moment-tensor radiation convention of :cite:t:`AkiRichards2002` (see Section :ref:`radiation_pattern`).

For derivation of formula :eq:`seismic_moment_homogeneous`, see Section :ref:`derivation_seismic_moment_homo`.

The exponential term :math:`\exp(\pi f t^*)` corrects for intrinsic attenuation using the attenuation operator :math:`t^*` (see Section :ref:`intrinsic_attenuation`).

Because P-wave velocity is typically higher than S-wave velocity, for the same propagation path and :math:`Q` the term :math:`t^*=r/(vQ)` is smaller for P waves, so the attenuation correction :math:`\exp(\pi f t^*)` is closer to unity. 
In practice, detectability is also controlled by radiation pattern and noise characteristics; network-design sensitivity is therefore often evaluated separately for P and S phases :cite:p:`HalloEisner2013`.

----


.. _derivation_seismic_moment_homo:

Derivation of the seismic moment in a homogeneous medium
========================================================

Here we derive Equation :eq:`seismic_moment_homogeneous` from the far-field radiation of
a point moment-tensor source.

In an unbounded homogeneous isotropic medium, the far-field displacement produced by a
point source with moment time function :math:`M_0(t)` is, for the phase with
radiation-pattern factor :math:`R` and velocity :math:`v` (:cite:t:`AkiRichards2002`,
Section 4.3),

.. math::
    :label: far_field_displacement

    u(t) = \frac{R}{4\pi\rho v^3 r}\,\dot{M}_0\!\left(t - \frac{r}{v}\right),

where the :math:`1/r` factor is the geometrical spreading of a spherical wave in a
homogeneous medium and the dot denotes the time derivative.

Taking the Fourier transform and using the fact that the moment rate spectrum tends to
the scalar seismic moment at low frequency, :math:`|\dot{M}_0(f)| \to M_0` for
:math:`f \ll f_c`, the low-frequency plateau of the displacement amplitude spectrum is

.. math::
    :label: plateau_homo

    \Omega_0 = \frac{M_0\,|R|}{4\pi\rho v^3 r},

consistent with the source-model assumption of Section :ref:`spectral_conventions`.

Intrinsic attenuation multiplies the spectrum by the dissipation filter of
Section :ref:`intrinsic_attenuation`, so the spectrum actually observed at the receiver is

.. math::
    :label: observed_homo

    |U(f)| = \frac{M_0\,|R|}{4\pi\rho v^3 r}\,\exp\!\big(-\pi f\,t^*\big),
    \qquad t^* = \frac{r}{vQ}.

Solving Equation :eq:`observed_homo` for the seismic moment gives

.. math::

    M_0
    =
    \frac{4\pi\rho v^3 r}{|R|}\;
    |U(f)|\;
    \exp\!\left(\pi f\,\frac{r}{vQ}\right),

which is Equation :eq:`seismic_moment_homogeneous`.

.. note::

   The exponential appears with a **positive** exponent in the moment formula: the
   amplitude observed at the receiver has already been reduced by attenuation, so
   recovering the source moment means undoing that reduction.

   Note also that :math:`|U(f)|` is an amplitude **spectrum**. The conversion of a
   recorded noise level to :math:`|U(f)|` is carried out once, by the coefficient
   :math:`S(f)` of Section :ref:`detection_threshold`, and must not be applied a second
   time here.

----

.. _derivation_radiation_pattern:

Derivation of effective radiation pattern magnitudes
====================================================

For microseismic network design with unknown focal mechanisms, we utilize effective averaged radiation factors. 
While literature often name these as average magnitudes, they are mathematically evaluated as the **Root Mean Square (RMS)** averages over the entire focal sphere to preserve wave energy :cite:p:`BooreBoatwright1984`.

We assume a canonical double-couple (DC) source. 
In a coordinate system where the fault plane normal is aligned with the x-axis and the slip direction is aligned with the y-axis, the seismic moment tensor :math:`\mathbf{M}` is:

.. math::
    \mathbf{M} = M_0 \begin{pmatrix} 0 & 1 & 0 \\ 1 & 0 & 0 \\ 0 & 0 & 0 \end{pmatrix}.

Let :math:`\mathbf{\gamma}` be the unit take-off vector parameterized by polar angle :math:`\theta` and azimuthal angle :math:`\phi`:

.. math::
    \mathbf{\gamma} = \begin{pmatrix} \sin\theta\cos\phi \\ \sin\theta\sin\phi \\ \cos\theta \end{pmatrix}.

.. _p_wave_average:

P-wave average
--------------

The P-wave radiation pattern factor is the projection of the equivalent force :math:`\mathbf{M}\mathbf{\gamma}` onto the longitudinal polarization :math:`\mathbf{\gamma}`:

.. math::
    R_P = \frac{\mathbf{\gamma}^T \mathbf{M} \mathbf{\gamma}}{M_0} = 2 \sin^2\theta \sin\phi \cos\phi = \sin^2\theta \sin 2\phi.

To find the RMS average, we integrate the square of :math:`R_P` over the unit sphere (where the averaging operator is :math:`\frac{1}{4\pi} \int_0^{2\pi} \int_0^\pi \dots \sin\theta \, d\theta \, d\phi`):

.. math::
    \langle R_P^2 \rangle 
    = \frac{1}{4\pi} \int_0^{2\pi} \int_0^\pi \left(\sin^2\theta \sin 2\phi\right)^2 \sin\theta \, d\theta \, d\phi.

Separating the integrals:

.. math::
    \langle R_P^2 \rangle 
    = \frac{1}{4\pi} \left( \int_0^\pi \sin^5\theta \, d\theta \right) \left( \int_0^{2\pi} \sin^2 2\phi \, d\phi \right).

Evaluating the integrals yields :math:`16/15` for the polar part and :math:`\pi` for the azimuthal part:

.. math::
    \langle R_P^2 \rangle = \frac{1}{4\pi} \left(\frac{16}{15}\right) (\pi) = \frac{4}{15}.

Taking the square root provides the effective P-wave magnitude:

.. math::
    R_P^{\mathrm{rms}} = \sqrt{\frac{4}{15}} \approx 0.516 \approx 0.52.

.. _s_wave_average:

S-wave average 
--------------

For S-waves, the total radiation pattern squared, :math:`R_S^2`, is the squared magnitude of the transverse component of the equivalent force. This is the total equivalent force squared minus the longitudinal (P-wave) component squared:

.. math::
    R_S^2 = \frac{|\mathbf{M}\mathbf{\gamma}|^2}{M_0^2} - R_P^2.

First, we compute the squared magnitude of the normalized equivalent force:

.. math::
    \frac{|\mathbf{M}\mathbf{\gamma}|^2}{M_0^2} = (\sin\theta\sin\phi)^2 + (\sin\theta\cos\phi)^2 + 0^2 = \sin^2\theta.

Averaging this over the focal sphere:

.. math::
    \langle \frac{|\mathbf{M}\mathbf{\gamma}|^2}{M_0^2} \rangle 
    = \frac{1}{4\pi} \int_0^{2\pi} \int_0^\pi \sin^2\theta \sin\theta \, d\theta \, d\phi
    = \frac{1}{4\pi} \left( \frac{4}{3} \right) (2\pi) = \frac{2}{3}.

Subtracting the P-wave averaged from the total force average yields the total S-wave average:

.. math::
    \langle R_S^2 \rangle = \frac{2}{3} - \langle R_P^2 \rangle = \frac{10}{15} - \frac{4}{15} = \frac{6}{15} = \frac{2}{5}.

Taking the square root provides the effective total S-wave magnitude:

.. math::
    R_S^{\mathrm{rms}} = \sqrt{\frac{2}{5}} \approx 0.632 \approx 0.63.

.. _sv_sh_wave_average:

SV- and SH-wave average 
-----------------------

The total S-wave coefficient derived above describes the magnitude of the full transverse radiation vector.
It does **not** imply equal partition between the SV and SH components.

To obtain component-wise averages, we now switch to the standard fault-based angular convention of :cite:t:`AkiRichards2002`.
To avoid confusion with the spherical angles used above in the tensor-based derivation, we denote these fault-based angles by :math:`\Theta` and :math:`\Phi`.

In this convention, the standard double-couple far-field radiation-pattern expressions for P, SV, and SH waves are:

.. math::

   R_P(\Theta,\Phi) = \sin 2\Theta \cos\Phi,

.. math::

   R_{SV}(\Theta,\Phi) = \cos 2\Theta \cos\Phi,

.. math::

   R_{SH}(\Theta,\Phi) = -\cos\Theta \sin\Phi,

where :math:`\Theta` is the take-off angle and :math:`\Phi` is the azimuth in the fault-based coordinate system.

The effective component-wise coefficients are defined by RMS averaging over the focal sphere:

.. math::

   \langle R_{SV}^2 \rangle
   =
   \frac{1}{4\pi}
   \int_0^{2\pi}\int_0^\pi
   \cos^2 2\Theta \cos^2\Phi \sin\Theta\,d\Theta\,d\Phi,

.. math::

   \langle R_{SH}^2 \rangle
   =
   \frac{1}{4\pi}
   \int_0^{2\pi}\int_0^\pi
   \cos^2\Theta \sin^2\Phi \sin\Theta\,d\Theta\,d\Phi.

Using

.. math::

   \int_0^{2\pi}\cos^2\Phi\,d\Phi = \pi,
   \qquad
   \int_0^{2\pi}\sin^2\Phi\,d\Phi = \pi,

.. math::

   \int_0^\pi \cos^2 2\Theta \sin\Theta\,d\Theta = \frac{14}{15},
   \qquad
   \int_0^\pi \cos^2\Theta \sin\Theta\,d\Theta = \frac{2}{3},

we obtain

.. math::

   \langle R_{SV}^2 \rangle
   =
   \frac{1}{4\pi}\,\pi\,\frac{14}{15}
   =
   \frac{7}{30},

.. math::

   \langle R_{SH}^2 \rangle
   =
   \frac{1}{4\pi}\,\pi\,\frac{2}{3}
   =
   \frac{1}{6}.

Therefore, the RMS effective coefficients are

.. math::

   R_{SV}^{\mathrm{rms}}
   =
   \sqrt{\langle R_{SV}^2\rangle}
   =
   \sqrt{\frac{7}{30}}
   \approx 0.483,

.. math::

   R_{SH}^{\mathrm{rms}}
   =
   \sqrt{\langle R_{SH}^2\rangle}
   =
   \sqrt{\frac{1}{6}}
   \approx 0.408.

As expected, the total S-wave mean-square coefficient is the sum of the two orthogonal transverse components:

.. math::

   \langle R_S^2\rangle
   =
   \langle R_{SV}^2\rangle + \langle R_{SH}^2\rangle
   =
   \frac{7}{30} + \frac{1}{6}
   =
   \frac{2}{5}.

Hence

.. math::

   R_{S}^{\mathrm{rms}}
   =
   \sqrt{\langle R_S^2\rangle}
   =
   \sqrt{\frac{2}{5}}
   \approx 0.63.

.. note::

   Therefore, the commonly used value :math:`0.63` corresponds to the **combined S-wave amplitude**, not to SV alone and not to SH alone.
   PyNetDesign uses fixed RMS constants :math:`R_P^{\mathrm{rms}}=\sqrt{4/15}`, :math:`R_{SV}^{\mathrm{rms}}=\sqrt{7/30}` for explicit SV, :math:`R_{SH}^{\mathrm{rms}}=\sqrt{1/6}` for explicit SH, and evaluates both S branches for composite ``S`` detectability.

----

References
==========

.. bibliography::
   :style: unsrt
   :filter: docname in docnames
