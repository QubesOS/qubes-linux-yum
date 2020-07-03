LOCALDIR ?= $(PWD)

REPOS = r4.0-dom0-fc25 r4.0-vm-fc29 r4.0-vm-fc30 r4.0-vm-fc31 r4.0-vm-fc32 r4.1-vm-fc33 r4.0-vm-centos7 r4.0-vm-centos8
REPOS += r4.1-dom0-fc32 r4.1-vm-fc30 r4.1-vm-fc31 r4.1-vm-fc32 r4.1-vm-fc33 r4.1-vm-centos7 r4.1-vm-centos8

get-sources:
	@git submodule update --init --recursive

verify-sources:
	@true

repos: $(addprefix skeleton-,$(REPOS)) $(addprefix comps-,$(REPOS))

# If comps-{dom0,vm}.xml are not present, use default
# ones provided by qubes-meta-packages
comps-%: release=$(word 1,$(subst -, ,$(subst comps-,,$@)))
comps-%:
	@for package_set in dom0 vm; do \
		if [ ! -e $(LOCALDIR)/$(release)/comps-$$package_set.xml ]; then \
			cp $(LOCALDIR)/meta-packages/comps/comps-$$package_set.xml $(LOCALDIR)/$(release); \
		fi; \
	done

skeleton-%: release=$(word 1,$(subst -, ,$(subst skeleton-,,$@)))
skeleton-%: package_set=$(word 2,$(subst -, ,$(subst skeleton-,,$@)))
skeleton-%: dist=$(word 3,$(subst -, ,$(subst skeleton-,,$@)))
skeleton-%:
	@$(LOCALDIR)/create_skeleton.sh $(release) $(package_set) $(dist)
