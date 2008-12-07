## This package understands the following switches:
%bcond_without		fedora


%global username		toranon
%global uid			19
%global homedir			%_var/lib/%name
%global logdir			%_var/log/%name

%{!?release_func:%global release_func() %1%{?dist}}

Name:		tor
Version:	0.2.0.32
Release:	%release_func 1
Group:		System Environment/Daemons
License:	BSD
Summary:	Anonymizing overlay network for TCP (The onion router)
URL:		http://tor.eff.org
Requires:	%name-core = %version-%release
Requires:	%name-lsb  = %version-%release


%package core
Summary:	Core programs for tor
Group:		System Environment/Daemons
URL:		http://tor.eff.org
Source0:	http://tor.eff.org/dist/%name-%version.tar.gz
Source1:	http://tor.eff.org/dist/%name-%version.tar.gz.asc
Source2:	tor.logrotate
Source3:	update-geoip
Source4:	netfilter-ipv4.h
Patch1:		tor-0.2.0.32-geoippath.patch
BuildRoot:	%_tmppath/%name-%version-%release-root

BuildRequires:	libevent-devel openssl-devel transfig ghostscript
BuildRequires:	/usr/bin/latex
BuildRequires:	texlive-texmf-fonts
BuildRequires:	fedora-usermgmt-devel
Provides:		user(%username)  = %uid
Provides:		group(%username) = %uid
Requires:		init(%name)
Requires(pre):		/etc/logrotate.d
Requires(postun):	/etc/logrotate.d
%{?FE_USERADD_REQ}


%package lsb
Summary:	LSB initscripts for tor
Group:		System Environment/Daemons
Provides:	init(%name) = lsb
Requires:	%name-core =  %version-%release
Source10:	tor.lsb
BuildArch:		noarch
Requires(pre):		%name-core
Requires(postun):	lsb-core-noarch %name-core
Requires(post):		lsb-core-noarch
Requires(preun):	lsb-core-noarch


%description
Tor is a connection-based low-latency anonymous communication system.

Applications connect to the local Tor proxy using the SOCKS protocol. The
local proxy chooses a path through a set of relays, in which each relay
knows its predecessor and successor, but no others. Traffic flowing down
the circuit is unwrapped by a symmetric key at each relay, which reveals
the downstream relay.

Warnings: Tor does no protocol cleaning.  That means there is a danger
that application protocols and associated programs can be induced to
reveal information about the initiator. Tor depends on Privoxy and
similar protocol cleaners to solve this problem. This is alpha code,
and is even more likely than released code to have anonymity-spoiling
bugs. The present network is very small -- this further reduces the
strength of the anonymity provided. Tor is not presently suitable for
high-stakes anonymity.


%description core
Tor is a connection-based low-latency anonymous communication system.

This package provides the "tor" program, which serves as both a client
and a relay node.


%description lsb
Tor is a connection-based low-latency anonymous communication system.

This package contains the LSB compliant initscripts to start the "tor"
daemon.


%prep
%setup -q
%patch1 -p1 -b .geoippath

install -p -m0644 %SOURCE3 .

sed -i -e 's!^\(\# *\)\?DataDirectory .*!DataDirectory %homedir/.tor!' src/config/torrc.sample.in
cat <<EOF >>src/config/torrc.sample.in
Group %username
User  %username
EOF

mkdir -p linux
install -p -m0644 %SOURCE4 linux/netfilter_ipv4.h


%build
export ac_cv_header_linux_netfilter_ipv4_h=yes
export LDFLAGS='-Wl,--as-needed'
%configure
make %{?_smp_mflags}
make -C doc/design-paper tor-design.pdf


%install
rm -rf $RPM_BUILD_ROOT

make install DESTDIR=$RPM_BUILD_ROOT
mv $RPM_BUILD_ROOT%_sysconfdir/tor/torrc{.sample,}

mkdir -p $RPM_BUILD_ROOT{%_sysconfdir/logrotate.d,%_initrddir,%logdir,%homedir,%_var/run/%name,%_var/lib/tor-data}

install -p -m0755 %SOURCE10 $RPM_BUILD_ROOT%_initrddir/tor
install -p -m0644 %SOURCE2  $RPM_BUILD_ROOT%_sysconfdir/logrotate.d/tor

ln -s %_datadir/tor/geoip $RPM_BUILD_ROOT%_var/lib/tor-data/geoip


%pre core
%__fe_groupadd %uid -r %username &>/dev/null || :
%__fe_useradd  %uid -r -s /sbin/nologin -d %homedir -M          \
                    -c 'TOR anonymizing user' -g %username %username &>/dev/null || :

%postun core
%__fe_userdel  %username &>/dev/null || :
%__fe_groupdel %username &>/dev/null || :


%post lsb
/usr/lib/lsb/install_initd %_initrddir/tor

%preun lsb
test "$1" != 0 || %_initrddir/tor stop &>/dev/null || :
test "$1" != 0 || /usr/lib/lsb/remove_initd %_initrddir/tor

%postun lsb
test "$1"  = 0 || env -i %_initrddir/tor try-restart &>/dev/null


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc doc/HACKING doc/TODO
%doc doc/spec/*.txt
%doc doc/design-paper/tor-design.pdf
%doc %lang(de) doc/website/*.de
%doc %lang(en) doc/website/*.en
%doc %lang(es) doc/website/*.es
%doc %lang(fr) doc/website/*.fr
%doc %lang(it) doc/website/*.it
%doc %lang(pl) doc/website/*.pl
%doc %lang(pt) doc/website/*.pt
%doc %lang(ru) doc/website/*.ru
%doc %lang(zh-cn) doc/website/*.zh-cn
%doc doc/website/*.css


%files core
%defattr(-,root,root,-)
%doc AUTHORS LICENSE README ChangeLog
%doc ReleaseNotes
%doc update-geoip
%dir               %_sysconfdir/tor
%config(noreplace) %_sysconfdir/logrotate.d/tor
%attr(0700,%username,%username) %dir %homedir
%attr(0730,root,%username)      %dir %logdir
%attr(0640,root,%username) %config(noreplace) %_sysconfdir/tor/torrc
%_bindir/*
%_mandir/man1/*
%_datadir/tor
%dir %_var/lib/tor-data
%config(noreplace) %_var/lib/tor-data/geoip

%exclude %_bindir/torify
%exclude %_mandir/man1/torify*
%exclude %_sysconfdir/tor/tor-tsocks.conf


%files lsb
  %defattr(-,root,root,-)
  %config %_initrddir/*
  %attr(0755,%username,%username) %dir %_var/run/%name


%changelog
* Sun Dec  7 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.0.32-1
- updated to 0.2.0.32
- removed -setgroups patch; supplementary groups are now set upstream

* Sun Jul 20 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.2.0.30-1
- updated to 0.2.0.30; rediffed patches
- (re)enabled transparent proxy support by workarounding broken
  <linux/netfilter_ipv4.h> header
- moved the 'geoip' database to /var/lib/tor-data where it can be
  updated periodically
- built with -Wl,--as-needed

* Thu Jul 10 2008 Nikolay Vladimirov <nikolay@vladimiroff.com> - 0.1.2.19-3
- rebuild for new libevent

* Wed Feb 13 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.2.19-2
- added 'missingok' to logrotate script (#429402)

* Tue Feb 12 2008 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.2.19-1
- updated to 0.1.2.19
- use file based BR for latex
- improved 'status' method of initscript to return rc of 'pidofproc'
  instead of doing further manual tests.  Calling 'pidofproc' directly
  instead of within a subshell should workaround #432254 too.

* Sat Jan 26 2008 Alex Lancaster <alexlan[AT]fedoraproject org> - 0.1.2.18-4
- Update BuildRequires: tex(latex),
- BR: texlive-texmf-fonts seems also to be necessary

* Sat Jan 26 2008 Alex Lancaster <alexlan[AT]fedoraproject org> - 0.1.2.18-3
- Rebuild for new libevent.

* Thu Dec 06 2007 Release Engineering <rel-eng at fedoraproject dot org> - 0.1.2.18-2
- Rebuild for deps

* Tue Oct 30 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.2.18-1
- updated to 0.1.2.18

* Fri Aug 31 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.2.17-1
- updated to 0.1.2.17

* Sat Aug 25 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.2.16-2
- fixed open(2) issue

* Fri Aug  3 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.2.16-1
- updated to 0.1.2.16 (SECURITY)

* Sat Jul 28 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.2.15-1
- updated to 0.1.2.15

* Sat May 26 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.2.14-1
- updated to 0.1.2.14

* Wed Apr 25 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.2.13-1
- updated to 0.1.2.13
- minor cleanups; especially in the %%doc section

* Sun Apr  8 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.26-4
- rebuilt for (yet another) new libevent

* Mon Feb 26 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.26-3
- rebuilt for new libevent

* Wed Jan 24 2007 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.26-2
- updated -setgroups patch (#224090, thx to Sami Farin)

* Sun Dec 17 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.26-1
- updated to 0.1.1.26 (SECURITY)
- do not turn on logging by default; it's easier to say "we do not log
  anything" to the police instead of enumerating the logged event
  classes and trying to explain that they do not contain any valuable
  information

* Sun Nov 12 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.25-1
- updated to 0.1.1.25

* Thu Oct  5 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.24-1
- updated to 0.1.1.24

* Sat Sep 30 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.23-5
- updated to recent fedora-usermgmt
- minor cleanups
- require only 'lsb-core-noarch' instead of whole 'lsb'

* Tue Sep 26 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.23-4
- first FE release (review #175433)

* Mon Sep 25 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.23-3
- removed '.have-lsb' and related logic in logrotate script; check for
  existence of the corresponding initscript instead of
- fixed bare '%%' in changelog section

* Thu Sep 21 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.23-2
- simplified things yet more and removed tsocks/torify too
- build -lsb unconditionally

* Thu Sep 21 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.23-1
- simplified spec file and removed -initng and -minit stuff

* Sun Aug 13 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.23-0
- updated to 0.1.1.23

* Sat Jul  8 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.22-0
- updated to 0.1.1.22

* Tue Jun 13 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.21-0
- updated to 0.1.1.21

* Wed May 24 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.1.20-0
- updated to 0.1.1.20; adjusted %%doc file-list
- added (optional) -tsocks subpackage
- use the more modern %%bcond_with* for specifying optional features

* Sun Feb 19 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.0.17-0
- updated to 0.1.0.17

* Mon Jan 30 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.0.16-0.1
- renamed the current main-package into a '-core' subpackage and
  created a new main-package which requires both the 'tor-core'
  subpackage and this with the current default init-method. This
  allows 'yum install tor' to work better; because yum is not very
  smart, the old packaging might install unwanted packages else.

* Wed Jan  4 2006 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.0.16-0
- updated to 0.1.0.16

* Fri Dec 23 2005 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.0.15-1.11
- reworked the 'setgroups' patch so that 'tor' survives a SIGHUP
- (re)added the 'reload' functionality to the lsb initscript and use
  it in logrotate

* Fri Dec 23 2005 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.0.15-1.8
- added ChangeLog to %%doc
- made torrc not world-readable
- added logrotate script

* Thu Dec 22 2005 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.0.15-1.4
- updated initng scripts to initng-0.4.8 syntax
- tweaked some Requires(...):
- added ghostscript BuildRequires:
- install initng scripts into the correct dir

* Thu Dec 15 2005 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.0.15-1.2
- use relative UID of 19 instead of 18 due to conflicts with the
  'munin' package

* Wed Dec 14 2005 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.0.15-1.1
- added -minit subpackage

* Sat Dec 10 2005 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de> - 0.1.0.15-1
- initial build
