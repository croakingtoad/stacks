import json
import logging
from stacks.constants import ANNAS_ARCHIVE_DOMAINS, DOMAIN_STATE_FILE, CONFIG_PATH

logger = logging.getLogger(__name__)


def _read_domain_state():
    """Read the domain state file, returning an empty dict on any error."""
    try:
        if DOMAIN_STATE_FILE.exists():
            with open(DOMAIN_STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.debug(f"Failed to read domain state: {e}")
    return {}


def _write_domain_state(data):
    """Write data to the domain state file (merges with existing state)."""
    try:
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        existing = _read_domain_state()
        existing.update(data)
        with open(DOMAIN_STATE_FILE, 'w') as f:
            json.dump(existing, f)
    except Exception as e:
        logger.debug(f"Failed to write domain state: {e}")


def get_all_domains():
    """Get all Anna's Archive domains: hardcoded list plus any extras found via Wikipedia.

    The user's preferred_domain (if set) is guaranteed to be in the list even if it
    is not in the hardcoded fallback list, so it can be tried during rotation.
    """
    from stacks.utils.domainupdater import get_wiki_mirrors
    extras = get_wiki_mirrors()
    domains = ANNAS_ARCHIVE_DOMAINS + [d for d in extras if d not in ANNAS_ARCHIVE_DOMAINS]
    preferred = _read_domain_state().get('preferred_domain')
    if preferred and preferred not in domains:
        domains = [preferred] + domains
    return domains


def get_working_domain():
    """Get the starting domain for rotation.

    Priority: user preferred_domain > last_working_domain > first in list.
    """
    all_domains = get_all_domains()
    state = _read_domain_state()
    preferred = state.get('preferred_domain')
    if preferred and preferred in all_domains:
        logger.debug(f"Using preferred domain: {preferred}")
        return preferred
    last = state.get('last_working_domain')
    if last and last in all_domains:
        logger.debug(f"Using last known working domain: {last}")
        return last
    logger.debug(f"Using default domain: {all_domains[0]}")
    return all_domains[0]


def save_working_domain(domain):
    """Save the last known working domain to state file."""
    _write_domain_state({'last_working_domain': domain})
    logger.info(f"Saved working domain: {domain}")


def save_preferred_domain(domain):
    """Persist the user's preferred domain.  Pass None to clear the preference."""
    state = _read_domain_state()
    if domain:
        state['preferred_domain'] = domain
    else:
        state.pop('preferred_domain', None)
    try:
        CONFIG_PATH.mkdir(parents=True, exist_ok=True)
        with open(DOMAIN_STATE_FILE, 'w') as f:
            json.dump(state, f)
        logger.info(f"Saved preferred domain: {domain}")
    except Exception as e:
        logger.debug(f"Failed to save preferred domain: {e}")


def get_next_domain(current_domain):
    """Get the next domain in the rotation after the current one."""
    all_domains = get_all_domains()
    try:
        current_index = all_domains.index(current_domain)
        next_index = (current_index + 1) % len(all_domains)
        next_domain = all_domains[next_index]
        logger.debug(f"Rotating from {current_domain} to {next_domain}")
        return next_domain
    except (ValueError, IndexError):
        logger.debug(f"Invalid current domain {current_domain}, using default")
        return all_domains[0]


def try_domains_until_success(func, *args, **kwargs):
    """
    Try a function with different Anna's Archive domains until one succeeds.

    The function should accept a 'domain' parameter.
    This will try the last working domain first, then rotate through all others.
    When successful, it saves the working domain for future use.

    Args:
        func: Function to call that accepts a 'domain' parameter
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func (domain will be added/overridden)

    Returns:
        The result of the successful function call

    Raises:
        The last exception encountered if all domains fail
    """
    all_domains = get_all_domains()

    # Start with the last working domain
    current_domain = get_working_domain()
    tried_domains = []
    last_error = None

    # Try all domains
    for _ in range(len(all_domains)):
        if current_domain in tried_domains:
            current_domain = get_next_domain(current_domain)
            continue

        tried_domains.append(current_domain)
        logger.debug(f"Trying domain: {current_domain}")

        try:
            # Call the function with the current domain
            kwargs['domain'] = current_domain
            result = func(*args, **kwargs)

            # Success! Save this domain for future use
            save_working_domain(current_domain)
            logger.info(f"Successfully used domain: {current_domain}")
            return result

        except Exception as e:
            logger.warning(f"Failed with domain {current_domain}: {e}")
            last_error = e
            current_domain = get_next_domain(current_domain)

    # All domains failed
    logger.error(f"All Anna's Archive domains failed. Last error: {last_error}")
    raise last_error if last_error else Exception("All domains failed")
