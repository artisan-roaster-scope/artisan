Name: artisan
Version: 0.5.0-0b1
Release:	1%{?dist}
Summary: Visual scope for coffee roasters

Group: Utilities
License: GPLv3
URL: http://code.google.com/p/artisan/
Source0:	
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires: PyQT4
Requires: PyQT4
Requires: numpy
Requires: python-matplotlib
Requires: scipy

%description
This software helps coffee roasters record, analyze, and control roast
profiles. With the help of a thermocouple data logger, or a
proportional–integral–derivative controller (PID controller), this software
offers roasting metrics to help make decisions that influence the final coffee
flavor.


%prep
%setup -q


%build
%configure
# nothing to do here

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/share/artisan
mkdir -p $RPM_BUILD_ROOT/usr/share/artisan/const
mkdir -p $RPM_BUILD_ROOT/usr/share/artisan/translations
install -o root -m 644 artisan.py $RPM_BUILD_ROOT/usr/share/artisan/artisan.py
install -o root -m 644 artisan.png $RPM_BUILD_ROOT/usr/share/artisan/artisan.png
install -o root -m 644 artisan.desktop $RPM_BUILD_ROOT/usr/share/applications/artisan.desktop
install -o root -m 644 const/__init__.py $RPM_BUILD_ROOT/usr/share/artisan/const/__init__.py
install -o root -m 644 const/UIconst.py $RPM_BUILD_ROOT/usr/share/artisan/const/UIconst.py
install -o root -m 644 translations/artisan_de.qm $RPM_BUILD_ROOT/usr/share/artisan/translations/artisan_de.qm
install -o root -m 644 translations/artisan_es.qm $RPM_BUILD_ROOT/usr/share/artisan/translations/artisan_es.qm
install -o root -m 644 translations/artisan_fr.qm $RPM_BUILD_ROOT/usr/share/artisan/translations/artisan_fr.qm
install -o root -m 644 translations/artisan_it.qm $RPM_BUILD_ROOT/usr/share/artisan/translations/artisan_it.qm
install -o root -m 644 translations/artisan_sv.qm $RPM_BUILD_ROOT/usr/share/artisan/translations/artisan_sv.qm
install -o root -m 755 debian/artisan.sh $RPM_BUILD_ROOT/usr/bin/artisan.sh

#make install DESTDIR=$RPM_BUILD_ROOT


%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc



%changelog
* Sun May 27 2011 lukas <lukas@einfachkaffee.de> - 0.5.0-0b1
  - support for Mac OS X 10.4 and PPC added
  - added more translations
  - added wheel graph editor
  - added custom event-control buttons
  - added Omega HHM28 multimeter device support
  - added support for devices with 4 thermocouples
  - added PID duty cycle
  - added math plotter in Extras
  - added run-time multiple device compatibility and symbolic expressions support
  - improved configuration of Axes
  - improved configuration of PID
  - improved Arduino code
  - bug fixes

